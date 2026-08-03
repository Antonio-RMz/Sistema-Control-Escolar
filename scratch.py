import pymysql
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Let's try empty password, or let's use app.config.conexion
    'db': 'escuelaBTI',
    'port': 3306,
    'cursorclass': pymysql.cursors.DictCursor
}

# Let's use the actual app config to connect to be sure we get the right config
from app.config.conexion import get_connection

def check_table():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DESCRIBE tb_materias")
        result = cursor.fetchall()
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")

check_table()
