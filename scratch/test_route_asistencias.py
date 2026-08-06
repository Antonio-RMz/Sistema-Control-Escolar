import sys
import os
import io
import datetime
import pandas as pd
import importlib.util

# Cargar app.py dinámicamente para evitar conflictos con la carpeta app/
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app_py_path = os.path.join(parent_dir, 'app.py')

sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location("app_module", app_py_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app

import pymysql
from app.config.conexion import get_connection

def run_test():
    app.testing = True
    
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
        with conn.cursor() as cursor:
            # 2. Insertar docente temporal con ID 9999
            cursor.execute("""
                INSERT INTO tb_docentes (idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, statusDocente)
                VALUES (9999, 'Docente de Prueba Excel', 'A', 'B', 'ACTIVO')
            """)
            conn.commit()
            print("Docente de prueba insertado con ID 9999")

        # 3. Simular la subida del archivo por POST a /asistencias/upload
        with app.test_client() as client:
            print("Simulando POST /asistencias/upload...")
            data = {
                "file": (excel_stream, "asistencias_agosto.xlsx")
            }
            res_upload = client.post("/asistencias/upload", data=data, content_type="multipart/form-data")
            print("Status POST:", res_upload.status_code)
            print("Response POST:", res_upload.get_json())
            assert res_upload.status_code == 200
            assert res_upload.get_json()["registros_procesados"] == 2
            
            # 4. Simular la consulta por GET a /asistencias
            print("\nSimulando GET /asistencias...")
            res_get = client.get("/asistencias?fecha_inicio=2026-08-01&fecha_fin=2026-08-03&id_docente=9999")
            print("Status GET:", res_get.status_code)
            records = res_get.get_json()
            print("Records:", records)
            assert res_get.status_code == 200
            assert len(records) == 2
            
            # Verificar estructura de los registros
            rec1 = next(r for r in records if r['fecha'] == '2026-08-01')
            assert rec1['docente'] == 'Docente de Prueba Excel A B'
            assert rec1['hora_entrada'] == '08:00:00'
            assert rec1['hora_salida'] == '18:00:00'
            assert rec1['horas_trabajadas'] == 10
            
            rec2 = next(r for r in records if r['fecha'] == '2026-08-02')
            assert rec2['docente'] == 'Docente de Prueba Excel A B'
            assert rec2['hora_entrada'] == '08:15:00'
            assert rec2['hora_salida'] == '17:45:00'
            assert rec2['horas_trabajadas'] == 9.5

            print("\n¡INTEGRACIÓN DE RUTAS PROCESADA CON ÉXITO!")

            # 5. Limpieza
            print("\nLimpiando base de datos...")
            with conn.cursor() as cursor:
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
