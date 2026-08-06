import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, statusDocente FROM tb_docentes")
            print("--- ALL TEACHERS ---")
            for doc in cursor.fetchall():
                print(doc)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
