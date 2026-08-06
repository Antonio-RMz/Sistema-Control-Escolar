import sys
import os
import io
import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection
from app.services.asistencias_service import AsistenciasService

def run_test():
    # 1. Crear un excel en memoria con la estructura descrita
    rows = [
        ["Reporte de Eventos de Asistencia"] + [""] * 20,
        [""] * 21,
        ["Periodo: 2026-08-01 ~ 2026-08-03"] + [""] * 20,
        ["1", "2", "3"] + [""] * 18,
        # Fila 5: ID, Nombre en col K (indice 10)
        ["ID:", "9999", "", "", "", "", "", "", "", "Nombre:", "Docente de Prueba Excel"] + [""] * 10,
        # Fila 6: Horas en col A (dia 1) y col B (dia 2)
        ["08:00\n18:00", "08:15\n12:00\n17:45", "", "", "", "", "", "", "", "", ""] + [""] * 10
    ]
    df = pd.DataFrame(rows)
    
    excel_stream = io.BytesIO()
    with pd.ExcelWriter(excel_stream, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Reporte de Asistencia", index=False, header=False)
    excel_stream.seek(0)
    
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 2. Insertar docente temporal con ID 9999
            cursor.execute("""
                INSERT INTO tb_docentes (idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, statusDocente)
                VALUES (9999, 'Docente de Prueba Excel', 'A', 'B', 'ACTIVO')
            """)
            conn.commit()
            print("Docente de prueba insertado con ID 9999")

            # 3. Procesar excel usando el servicio
            print("Procesando excel...")
            registros = AsistenciasService.procesar_excel(excel_stream)
            print(f"Registros procesados reportados: {registros}")
            assert registros == 2, f"Se esperaban 2 registros procesados, se reportaron {registros}"

            # 4. Validar registros en tb_asistencias_docentes
            cursor.execute("SELECT * FROM tb_asistencias_docentes WHERE id_docente = 9999 ORDER BY fecha")
            asistencias = cursor.fetchall()
            print("Asistencias guardadas en la base de datos:", asistencias)
            
            assert len(asistencias) == 2, f"Se esperaban 2 registros de asistencia, se obtuvieron {len(asistencias)}"
            
            # Registro 1: 2026-08-01
            r1 = asistencias[0]
            assert r1['fecha'] == datetime.date(2026, 8, 1)
            assert r1['hora_entrada'] == datetime.timedelta(hours=8)
            assert r1['hora_salida'] == datetime.timedelta(hours=18)
            assert float(r1['horas_trabajadas']) == 10.0
            
            # Registro 2: 2026-08-02
            r2 = asistencias[1]
            assert r2['fecha'] == datetime.date(2026, 8, 2)
            assert r2['hora_entrada'] == datetime.timedelta(hours=8, minutes=15)
            assert r2['hora_salida'] == datetime.timedelta(hours=17, minutes=45)
            assert float(r2['horas_trabajadas']) == 9.5
            
            print("\n¡TODAS LAS ASERCIONES DEL PARSER PASARON CON ÉXITO!")

            # 5. Limpieza
            print("\nLimpiando base de datos...")
            cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente = 9999")
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = 9999")
            conn.commit()
            print("Limpieza completada.")

    except Exception as e:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente = 9999")
                cursor.execute("DELETE FROM tb_docentes WHERE idDocente = 9999")
                conn.commit()
        except:
            pass
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
