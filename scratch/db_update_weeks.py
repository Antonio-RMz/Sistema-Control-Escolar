import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def update_db():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Add duracionSemanas to tb_niveles_academicos if it doesn't exist
            cursor.execute("DESCRIBE tb_niveles_academicos")
            cols = [col['Field'] for col in cursor.fetchall()]
            if 'duracionSemanas' not in cols:
                cursor.execute("""
                    ALTER TABLE tb_niveles_academicos 
                    ADD COLUMN duracionSemanas INT NOT NULL DEFAULT 13
                """)
                print("Column 'duracionSemanas' added to 'tb_niveles_academicos'.")
            else:
                print("Column 'duracionSemanas' already exists in 'tb_niveles_academicos'.")
            
            # 2. Update semester rows to have 26 weeks, and trimesters to have 13 weeks
            cursor.execute("""
                UPDATE tb_niveles_academicos 
                SET duracionSemanas = 13 
                WHERE nombre LIKE '%Trimestre%'
            """)
            cursor.execute("""
                UPDATE tb_niveles_academicos 
                SET duracionSemanas = 26 
                WHERE nombre LIKE '%Semestre%'
            """)
            print("duracionSemanas updated for trimesters (13) and semesters (26).")
            
            conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_db()
