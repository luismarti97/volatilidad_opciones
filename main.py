import streamlit as st
import plotly.express as px
from utils import obtener_dataframes, volatilidad_implicita_df

st.sidebar.title("Análisis de Volatilidad Implícita de las opciones MINI IBEX")

if st.sidebar.button("Cargar y Calcular Datos"):
    url = 'https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35'
    df_opciones, df_futuros = obtener_dataframes(url)
    st.session_state.resultado_volatilidad = volatilidad_implicita_df(df_opciones, df_futuros)
    st.success("Datos cargados y volatilidad calculada con éxito!")

if 'resultado_volatilidad' in st.session_state:
    tipo_de_opcion = st.sidebar.selectbox("Selecciona el tipo de opción", ['Call', 'Put'])
    fechas_disponibles = st.session_state.resultado_volatilidad['Fecha'].unique()
    fecha = st.sidebar.selectbox("Selecciona la fecha", fechas_disponibles)
    # mostrar datos filtrados 
    st.write(st.session_state.resultado_volatilidad[(st.session_state.resultado_volatilidad['Fecha'] == fecha) & (st.session_state.resultado_volatilidad['Tipo'] == tipo_de_opcion)][['Strike', 'Volatilidad']])
    
    df_filtrado = st.session_state.resultado_volatilidad[(st.session_state.resultado_volatilidad['Fecha'] == fecha) & (st.session_state.resultado_volatilidad['Tipo'] == tipo_de_opcion)]
    line_color = 'green' if tipo_de_opcion == 'Call' else 'red'
    fig = px.line(df_filtrado, x='Strike', y='Volatilidad', title=f'IV Curves on {fecha} for {tipo_de_opcion} Options',
                  labels={'Strike': 'Strike Price', 'Volatilidad': 'Implied Volatility'}, markers=True)
    fig.update_traces(line_color=line_color)
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.sidebar.write("Carga los datos para comenzar el análisis.")
    