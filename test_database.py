import os
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
from utils import obtener_dataframes, volatilidad_implicita_df

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector package.
    """
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.

    instance_connection_name =  "miniibex-project:us-central1:miniibex-sql" # e.g. 'project:region:instance'
    db_user = "miniibex-sql"# e.g. 'my-db-user'
    db_pass = "ferneyan23"  # e.g. 'my-db-password'
    db_name = "mb"   # e.g. 'my-database'

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        # ...
    )
    return pool

def create_sample_table(engine):
    # SQL statement for creating a table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_table (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        value FLOAT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    with engine.connect() as connection:
        connection.execute(sqlalchemy.text(create_table_query))
        print("Table 'test_table' created successfully.")


def guardar_opciones_futuros(engine, df_opciones, df_futuros):
    df_opciones.to_sql('opciones', con=engine, if_exists='append', index=False)
    df_futuros.to_sql('futuros', con=engine, if_exists='append', index=False)

def guardar_volatilidad(engine, df_volatilidad):
    df_volatilidad.to_sql('volatilidad', con=engine, if_exists='append', index=False)


if __name__ == "__main__":
    engine = connect_with_connector()  # Conectar a la base de datos
    url = 'https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35'
    df_opciones, df_futuros = obtener_dataframes(url)
    guardar_opciones_futuros(engine, df_opciones, df_futuros)
    
    df_volatilidad = volatilidad_implicita_df(df_opciones, df_futuros)
    guardar_volatilidad(engine, df_volatilidad)
