import pymysql
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'db': 'escuelaBTI',
    'port': 3306,
    'cursorclass': pymysql.cursors.DictCursor
}

def check_table():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DESCRIBE curso_extra_alumno")
        result = cursor.fetchall()
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")

check_table()
