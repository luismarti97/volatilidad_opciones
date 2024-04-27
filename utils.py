import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import mibian
from datetime import datetime

def obtener_dataframes(url):
    # Hacer la solicitud GET y obtener el contenido HTML
    response = requests.get(url)
    html = response.text
    
    # Crear un objeto BeautifulSoup para analizar el HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Encuentra todas las filas de la tabla que contengan "OPE" o "OCE" en el atributo 'data-tipo'
    rows = soup.find_all('tr', {'data-tipo': lambda value: value and (value.startswith('OPE') or value.startswith('OCE'))})

    # Prepara listas para almacenar datos separados
    ope_data = []
    oce_data = []

    # Itera sobre las filas y extrae los datos
    for row in rows:
        cells = row.find_all('td')
        cell_data = [cell.get_text(strip=True) for cell in cells]
        # Extrae la fecha y el tipo
        data_tipo = row.get('data-tipo')
        data_type, date = data_tipo[:3], data_tipo[3:]

        # Clasifica los datos en OPE o OCE
        if data_type == 'OPE':
            ope_data.append([date] + cell_data)
        elif data_type == 'OCE':
            oce_data.append([date] + cell_data)

    # Crea DataFrames de pandas para cada conjunto de datos
    df_put = pd.DataFrame(ope_data)
    df_call = pd.DataFrame(oce_data)

    # Si la primera columna es la fecha, establecerla como índice
    df_put.set_index(0, inplace=True)
    df_call.set_index(0, inplace=True)

    # Cambia los valores vacíos por NaN y elimina filas con NaN
    df_put.replace({"": np.nan, "-": np.nan}, inplace=True)
    df_call.replace({"": np.nan, "-": np.nan}, inplace=True)
    df_put.dropna(subset=[df_put.columns[-1]], inplace=True)
    df_call.dropna(subset=[df_call.columns[-1]], inplace=True)

    # Selecciona las columnas de interés y renombra las columnas
    df_put = df_put.iloc[:, [0, -1]].copy()
    df_call = df_call.iloc[:, [0, -1]].copy()
    df_put.columns = ['Strike', 'Anterior']
    df_call.columns = ['Strike', 'Anterior']

    # Convierte las columnas a formato numérico
    df_put['Strike'] = df_put['Strike'].str.replace('.', '').str.replace(',', '.').astype(float)
    df_call['Strike'] = df_call['Strike'].str.replace('.', '').str.replace(',', '.').astype(float)
    df_put['Anterior'] = df_put['Anterior'].str.replace('.', '').str.replace(',', '.').astype(float)
    df_call['Anterior'] = df_call['Anterior'].str.replace('.', '').str.replace(',', '.').astype(float)

    # Convierte la fecha al formato adecuado y establece como índice
    df_put.index = pd.to_datetime(df_put.index, format='%Y%m%d')
    df_call.index = pd.to_datetime(df_call.index, format='%Y%m%d')
    
  
    # Extracción de datos de la tabla de futuros
    tabla_futuros = soup.find('table', { 'id':"Contenido_Contenido_tblFuturos"})
    futuros_list = []

    # Iterar sobre cada fila de la tabla excepto la cabecera
    for fila in tabla_futuros.find('tbody').find_all('tr', class_="text-right"):
        datos_fila = [celda.text.strip() for celda in fila.find_all('td')]
        futuro = {
                'Vencimiento' : datos_fila[0],
                'Anterior': datos_fila[13]
            }
        futuros_list.append(futuro)

    # Convertir la lista de diccionarios en un DataFrame de pandas
    df_futuros = pd.DataFrame(futuros_list)
    
    # Procesamiento adicional de futuros
    df_futuros['Anterior'] = df_futuros['Anterior'].str.replace('.', '').str.replace(',', '.').astype(float)
    df_futuros['Vencimiento'] = pd.to_datetime(df_futuros['Vencimiento'], format='%d %b. %Y')

    # Crear un DataFrame de opciones combinando calls y puts
    df_call['Tipo'] = 'Call'
    df_put['Tipo'] = 'Put'
    df_opciones = pd.concat([df_call, df_put])
    
    return df_opciones, df_futuros


def volatilidad_implicita_df(df, tabla_futuros):
    # Calcula la volatilidad implícita
    precio_subyacente = tabla_futuros['Anterior'].iloc[0]
    today_date = datetime.now()
    resultados = []

    for fecha, row in df.iterrows():
        strike = row['Strike']
        if row['Anterior'] == '-':
            continue
        precio_opcion = row['Anterior']
        tipo_de_opcion = row['Tipo']

        days_to_expiration = (pd.to_datetime(fecha) - today_date).days
        c = mibian.BS([precio_subyacente, strike, 0, days_to_expiration], callPrice=precio_opcion if tipo_de_opcion == 'Call' else None, putPrice=precio_opcion if tipo_de_opcion == 'Put' else None)
        resultados.append({
            'Fecha': fecha.strftime('%d-%m-%Y'),
            'Strike': strike,
            'Volatilidad': c.impliedVolatility,
            'Tipo': tipo_de_opcion
        })
    
    return pd.DataFrame(resultados)


