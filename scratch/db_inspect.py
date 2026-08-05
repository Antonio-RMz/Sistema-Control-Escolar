import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT idAlumno, nombre, apPaterno, idGrupo 
                FROM tb_alumnos 
                WHERE idGrupo IS NOT NULL
                LIMIT 20
            """)
            print("--- STUDENTS WITH idGrupo IS NOT NULL ---")
            for student in cursor.fetchall():
                print(student)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
