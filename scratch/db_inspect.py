import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_grupos LIMIT 5")
            groups = cursor.fetchall()
            print("\n--- GROUPS ---")
            for g in groups:
                print(g)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
