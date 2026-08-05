import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def setup_database():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Create tb_niveles_academicos table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tb_niveles_academicos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL
                )
            """)
            print("Table 'tb_niveles_academicos' verified/created.")

            # Insert default values if empty
            cursor.execute("SELECT COUNT(*) as count FROM tb_niveles_academicos")
            count = cursor.fetchone()['count']
            if count == 0:
                niveles = [
                    "1er Trimestre", "2do Trimestre", "3er Trimestre", 
                    "4to Trimestre", "5to Trimestre", "6to Trimestre",
                    "7mo Trimestre", "8vo Trimestre", "9no Trimestre", "10mo Trimestre",
                    "1er Semestre", "2do Semestre", "3er Semestre", "4to Semestre",
                    "5to Semestre", "6to Semestre", "7mo Semestre", "8vo Semestre"
                ]
                for n in niveles:
                    cursor.execute("INSERT INTO tb_niveles_academicos (nombre) VALUES (%s)", (n,))
                print("Default academic levels inserted.")

            # 2. Add id_nivel_academico column to tb_grupos if it doesn't exist
            cursor.execute("DESCRIBE tb_grupos")
            columns = [col['Field'] for col in cursor.fetchall()]
            if 'id_nivel_academico' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_grupos 
                    ADD COLUMN id_nivel_academico INT NULL,
                    ADD CONSTRAINT fk_grupo_nivel FOREIGN KEY (id_nivel_academico) REFERENCES tb_niveles_academicos(id)
                """)
                print("Column 'id_nivel_academico' added to 'tb_grupos'.")
            else:
                print("Column 'id_nivel_academico' already exists in 'tb_grupos'.")

            conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    setup_database()
