import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def create_table():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Crear la tabla tb_asistencias_docentes si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tb_asistencias_docentes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_docente INT NOT NULL,
                    fecha DATE NOT NULL,
                    hora_entrada TIME NOT NULL,
                    hora_salida TIME NOT NULL,
                    horas_trabajadas DECIMAL(5,2) NOT NULL,
                    FOREIGN KEY (id_docente) REFERENCES tb_docentes(idDocente) ON DELETE CASCADE,
                    UNIQUE KEY unique_docente_fecha (id_docente, fecha)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conn.commit()
            print("Table 'tb_asistencias_docentes' created or already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    create_table()
