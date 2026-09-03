import sys
import os
import datetime
import pandas as pd
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection
from app.services.asistencias_service import AsistenciasService
from app.services.personal_service import PersonalService

def test_flow():
    print("=== INICIANDO PRUEBA DE SERVICIO SOCIAL ===")
    
    # 1. Crear personal de prueba en la base de datos
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    id_personal = None
    try:
        # Limpiar si ya existe
        cursor.execute("DELETE FROM tb_personal WHERE usuario = 'test_ss_user'")
        conn.commit()
        
        # Insertar personal
        data_personal = {
            "nombre": "Estudiante SS de Prueba",
            "usuario": "test_ss_user",
            "password": "testpassword",
            "rol": "Servicio Social",
            "status": "ACTIVO",
            "idBiometrico": "999",
            "es_servicio_social": 1,
            "horas_objetivo": 400
        }
        res_create = PersonalService.create_personal(data_personal)
        if "error" in res_create:
            print(f"Error al crear personal: {res_create['error']}")
            return
            
        id_personal = res_create["idPersonal"]
        print(f"Personal de prueba creado con ID: {id_personal}")
        
        # 2. Generar Excel de prueba en memoria
        # Estructura del excel:
        # Fila 0: ["Periodo: 2026-08-01 ~ 2026-08-06", "", "", "", "", ""]
        # Fila 1: ["ID:", "999", "Nombre:", "Estudiante SS de Prueba", "", ""]
        # Fila 2: ["14:00 14:01 17:00", "09:00 13:30", "08:00", "", "", ""] (marcajes diarios)
        
        excel_data = [
            ["Periodo: 2026-08-01 ~ 2026-08-06", None, None, None, None, None],
            ["ID:", "999", "Nombre:", "Estudiante SS de Prueba", None, None],
            ["14:00 14:01 17:00", "09:00 13:30", "08:00", None, None, None]
        ]
        df_mock = pd.DataFrame(excel_data)
        
        # Escribir el DataFrame en un buffer BytesIO de Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_mock.to_excel(writer, sheet_name="Reporte de Asistencia", index=False, header=False)
        excel_buffer.seek(0)
        
        # 3. Procesar el Excel ficticio
        print("\nProcesando Excel ficticio...")
        processed_count = AsistenciasService.procesar_excel(excel_buffer)
        print(f"Marcajes procesados: {processed_count}")
        
        # 4. Consultar resultados en tb_asistencias_personal
        cursor.execute("SELECT * FROM tb_asistencias_personal WHERE id_personal = %s ORDER BY fecha ASC", (id_personal,))
        records = cursor.fetchall()
        print("\n=== REGISTROS DE ASISTENCIA EN BASE DE DATOS ===")
        for r in records:
            print(f"Fecha: {r['fecha']} | Entrada: {r['hora_entrada']} | Salida: {r['hora_salida']} | Horas: {r['horas_trabajadas']} | Estado: {r['estado']} | Obs: {r['observaciones']}")
            
        # Verificar cálculos esperados
        # Registro 1 (2026-08-01): Entrada 14:00, Salida 17:00, Horas 3.00, Estado Completo (el marcaje 14:01 debe descartarse/filtrarse)
        # Registro 2 (2026-08-02): Entrada 09:00, Salida 13:30, Horas 4.50, Estado Completo
        # Registro 3 (2026-08-03): Entrada 08:00, Salida 00:00, Horas 0.00, Estado Incompleto
        
        assert len(records) == 3, f"Se esperaban 3 registros, se encontraron {len(records)}"
        
        # Registro 1
        assert float(records[0]['horas_trabajadas']) == 3.0, "Registro 1: Horas incorrectas"
        assert records[0]['estado'] == 'Completo', "Registro 1: Estado incorrecto"
        
        # Registro 2
        assert float(records[1]['horas_trabajadas']) == 4.5, "Registro 2: Horas incorrectas"
        assert records[1]['estado'] == 'Completo', "Registro 2: Estado incorrecto"
        
        # Registro 3
        assert float(records[2]['horas_trabajadas']) == 0.0, "Registro 3: Horas incorrectas"
        assert records[2]['estado'] == 'Incompleto', "Registro 3: Estado incorrecto"
        
        print("\n[OK] Validaciones de base de datos correctas!")

        # 5. Probar el servicio de consulta
        print("\nConsultando acumulados y reportes...")
        report = AsistenciasService.get_asistencias_personal("2026-08-01", "2026-08-06", id_personal)
        print("=== REPORTE DIARIO ===")
        for a in report["asistencias"]:
            print(f"Fecha: {a['fecha']} | Horas: {a['horas_trabajadas']} | Estado: {a['estado']}")
        print("=== RESUMEN ACUMULADO ===")
        for r in report["resumen"]:
            print(f"Personal: {r['nombre']} | Rol: {r['rol']} | Es SS: {r['es_servicio_social']} | Horas Periodo: {r['horas_periodo']} | Horas Totales Históricas: {r['horas_totales']} | Horas Restantes: {r['horas_restantes']} | Progreso: {r['porcentaje_progreso']}%")

        assert len(report["asistencias"]) == 3
        assert len(report["resumen"]) == 1
        assert report["resumen"][0]["horas_periodo"] == 7.5
        assert report["resumen"][0]["horas_totales"] == 7.5
        assert report["resumen"][0]["horas_restantes"] == 392.5
        assert report["resumen"][0]["porcentaje_progreso"] == 1.9
        
        print("\n[OK] Validaciones del reporte correctas!")
        print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")

    except Exception as e:
        print(f"\n[FAIL] Ocurrió un error en la prueba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza de datos de prueba
        if id_personal:
            print("\nLimpiando datos de prueba...")
            cursor.execute("DELETE FROM tb_asistencias_personal WHERE id_personal = %s", (id_personal,))
            cursor.execute("DELETE FROM tb_personal WHERE idPersonal = %s", (id_personal,))
            conn.commit()
        cursor.close()
        conn.close()

if __name__ == '__main__':
    test_flow()
