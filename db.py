import os
from pubsub import pub as bus
from datetime import datetime

import psycopg2

from topics import TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")

connection = None
cursor = None

def init_db():
    try:
        global connection
        connection = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )

        global cursor
        cursor = connection.cursor()

        create_table_query = '''
            CREATE TABLE IF NOT EXISTS measurement (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                address VARCHAR NOT NULL,
                soil_measure FLOAT NOT NULL,
                type VARCHAR NOT NULL,
                battery FLOAT
            );
        '''
        cursor.execute(create_table_query)
        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print("Błąd podczas łączenia z bazą danych:", error)


def insert_measurement_with_params(date, address, soil_measure, battery):
    try:
        insert_query = '''
            INSERT INTO measurement (date, address, soil_measure, type, battery)
            VALUES (%s, %s, %s, %s, %s);
        '''

        measurement_type = "v1 - debug"

        cursor.execute(insert_query, (date, address, soil_measure, measurement_type, battery))
        connection.commit()
        print("Pomiar został zapisany do bazy danych.")
    except (Exception, psycopg2.Error) as error:
        print("Błąd podczas zapisywania do bazy danych:", error)

def debug_soil_advetise(address: str, soil_moisture, battery):
    print("saving to db")
    try:
        insert_measurement_with_params(datetime.now(), address, soil_moisture, battery)
    except Exception:
        print("can't save to db")

bus.subscribe(debug_soil_advetise, TOPIC_D_SM_SOIL_MEASURE_ADVERTISEMENT)