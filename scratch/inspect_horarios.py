import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query some schedules
            cursor.execute("""
                SELECT h.id_docente, 
                       CONCAT(d.nombreDocente, ' ', d.apPaternoDocente, ' ', d.apMaternoDocente) as docente,
                       h.diaSemana, h.horaInicio, h.horaFin
                FROM tb_horarios h
                JOIN tb_docentes d ON h.id_docente = d.idDocente
                LIMIT 50
            """)
            rows = cursor.fetchall()
            print("--- HORARIOS SAMPLES ---")
            for r in rows:
                print(r)
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
