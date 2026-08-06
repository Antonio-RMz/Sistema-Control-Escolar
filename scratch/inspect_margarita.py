import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Find all teachers
            cursor.execute("SELECT idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, statusDocente FROM tb_docentes")
            teachers = cursor.fetchall()
            print("--- ALL TEACHERS ---")
            for t in teachers:
                print(t)
                
            cursor.execute("DESCRIBE tb_horarios")
            print("\n--- tb_horarios COLUMNS ---")
            for col in cursor.fetchall():
                print(col)
                
            cursor.execute("DESCRIBE tb_grupos")
            print("\n--- tb_grupos COLUMNS ---")
            for col in cursor.fetchall():
                print(col)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
