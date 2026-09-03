import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def migrate():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Check/Add columns to tb_personal
            cursor.execute("DESCRIBE tb_personal")
            columns = [col['Field'] if isinstance(col, dict) else col[0] for col in cursor.fetchall()]
            
            if 'idBiometrico' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_personal 
                    ADD COLUMN idBiometrico VARCHAR(50) NULL AFTER status
                """)
                print("Column 'idBiometrico' added to 'tb_personal'.")
            else:
                print("Column 'idBiometrico' already exists in 'tb_personal'.")
                
            if 'es_servicio_social' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_personal 
                    ADD COLUMN es_servicio_social TINYINT(1) DEFAULT 0 AFTER idBiometrico
                """)
                print("Column 'es_servicio_social' added to 'tb_personal'.")
            else:
                print("Column 'es_servicio_social' already exists in 'tb_personal'.")
                
            if 'horas_objetivo' not in columns:
                cursor.execute("""
                    ALTER TABLE tb_personal 
                    ADD COLUMN horas_objetivo INT NULL DEFAULT NULL AFTER es_servicio_social
                """)
                print("Column 'horas_objetivo' added to 'tb_personal'.")
            else:
                print("Column 'horas_objetivo' already exists in 'tb_personal'.")

            # 2. Create tb_asistencias_personal table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tb_asistencias_personal (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_personal INT NOT NULL,
                    fecha DATE NOT NULL,
                    hora_entrada TIME NOT NULL,
                    hora_salida TIME NOT NULL,
                    horas_trabajadas DECIMAL(5,2) NOT NULL,
                    estado VARCHAR(50) NOT NULL DEFAULT 'Completo',
                    observaciones TEXT NULL,
                    FOREIGN KEY (id_personal) REFERENCES tb_personal(idPersonal) ON DELETE CASCADE,
                    UNIQUE KEY unique_personal_fecha (id_personal, fecha)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            print("Table 'tb_asistencias_personal' verified/created.")
            
            conn.commit()
            print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
