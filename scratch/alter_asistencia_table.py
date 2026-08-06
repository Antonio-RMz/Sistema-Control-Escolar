import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def alter_table():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if columns already exist
            cursor.execute("DESCRIBE tb_asistencias_docentes")
            columns = [c['Field'] if isinstance(c, dict) else c[0] for c in cursor.fetchall()]
            
            if 'estado' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_asistencias_docentes 
                    ADD COLUMN estado VARCHAR(50) NOT NULL DEFAULT 'Completo'
                """)
                print("Column 'estado' added.")
            else:
                print("Column 'estado' already exists.")
                
            if 'observaciones' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_asistencias_docentes 
                    ADD COLUMN observaciones TEXT NULL
                """)
                print("Column 'observaciones' added.")
            else:
                print("Column 'observaciones' already exists.")
                
            conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    alter_table()
