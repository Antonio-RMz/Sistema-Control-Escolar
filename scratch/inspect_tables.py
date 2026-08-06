import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DESCRIBE tb_grupos")
            for col in cursor.fetchall():
                print(col)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
