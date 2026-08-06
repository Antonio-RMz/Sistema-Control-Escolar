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
    # 1. Crear un excel en memoria con los 3 casos
    # Periodo: Lunes 2026-08-03 a Lunes 2026-08-03
    rows = [
        ["Reporte de Eventos de Asistencia"] + [""] * 20,
        [""] * 21,
        ["Periodo: 2026-08-01 ~ 2026-08-03"] + [""] * 20,
        ["1", "2", "3"] + [""] * 18,
        
        # Guadalupe: ID 14
        ["ID:", "14", "", "", "", "", "", "", "", "Nombre:", "Lic. Guadalupe"] + [""] * 10,
        ["", "", "11:07\n12:06\n12:09\n16:46\n18:11\n18:11\n19:00", "", "", "", "", "", "", "", ""] + [""] * 10,
        
        # Margarita: ID 12
        ["ID:", "12", "", "", "", "", "", "", "", "Nombre:", "Lic. Margarita"] + [""] * 10,
        ["", "", "11:13\n15:05", "", "", "", "", "", "", "", ""] + [""] * 10,
        
        # Karen Itzel: ID 15
        ["ID:", "15", "", "", "", "", "", "", "", "Nombre:", "Lic. Karen Itzel"] + [""] * 10,
        ["", "", "12:07\n13:03\n13:03\n14:02\n14:02\n15:02", "", "", "", "", "", "", "", ""] + [""] * 10
    ]
    df = pd.DataFrame(rows)
    
    excel_stream = io.BytesIO()
    with pd.ExcelWriter(excel_stream, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Reporte de Asistencia", index=False, header=False)
    excel_stream.seek(0)
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. Crear grupo temporal
            cursor.execute("""
                INSERT INTO tb_grupos (id, clave, fechaCreacion, fechaInicio, fechaFin)
                VALUES (9999, 'GRP_TEST_COMPLEX', '2026-01-01', '2026-08-01', '2026-08-31')
                ON DUPLICATE KEY UPDATE id=id
            """)
            
            # Crear materia temporal
            cursor.execute("""
                INSERT INTO tb_materias (id, nombreMateria, estatusMateria)
                VALUES (9999, 'MATERIA_TEST_COMPLEX', 1)
                ON DUPLICATE KEY UPDATE id=id
            """)
            
            # Crear docentes temporales
            docentes = [
                (14, 'Guadalupe'),
                (12, 'Margarita'),
                (15, 'Karen Itzel')
            ]
            for doc_id, name in docentes:
                cursor.execute("""
                    INSERT INTO tb_docentes (idDocente, nombreDocente, statusDocente)
                    VALUES (%s, %s, 'ACTIVO')
                    ON DUPLICATE KEY UPDATE idDocente=idDocente
                """, (doc_id, f"Lic. {name}"))

            # Crear horarios
            # Guadalupe (14): Lunes (1): 11:00-12:00, 17:00-18:00, 18:00-19:00
            horarios_g = [
                (14, 1, '11:00:00', '12:00:00'),
                (14, 1, '17:00:00', '18:00:00'),
                (14, 1, '18:00:00', '19:00:00')
            ]
            # Margarita (12): Lunes (1): 11:00-12:00, 12:00-13:00, 13:00-14:00, 14:00-15:00
            horarios_m = [
                (12, 1, '11:00:00', '12:00:00'),
                (12, 1, '12:00:00', '13:00:00'),
                (12, 1, '13:00:00', '14:00:00'),
                (12, 1, '14:00:00', '15:00:00')
            ]
            # Karen Itzel (15): Lunes (1): 12:00-13:00, 13:00-14:00, 14:00-15:00
            horarios_k = [
                (15, 1, '12:00:00', '13:00:00'),
                (15, 1, '13:00:00', '14:00:00'),
                (15, 1, '14:00:00', '15:00:00')
            ]
            
            for h in horarios_g + horarios_m + horarios_k:
                cursor.execute("""
                    INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin)
                    VALUES (9999, 9999, %s, %s, %s, %s)
                """, h)
                
            conn.commit()
            print("Entidades y horarios temporales creados.")

        # 3. Ejecutar procesamiento
        print("Procesando excel de casos complejos...")
        registros = AsistenciasService.procesar_excel(excel_stream)
        print(f"Registros insertados/actualizados: {registros}")
        assert registros == 3, f"Se esperaban 3 registros procesados, se obtuvieron {registros}"

        # 4. Consultar resultados usando el servicio get_asistencias
        resultados = AsistenciasService.get_asistencias("2026-08-03", "2026-08-03")
        
        print("\n--- RESULTADOS OBTENIDOS ---")
        for res in resultados:
            print(res)

        # Aserción para Guadalupe (ID 14)
        g_res = next(r for r in resultados if r['id_docente'] == 14)
        assert g_res['horas_trabajadas'] == 2.88, f"Esperado 2.88 para Guadalupe, obtenido {g_res['horas_trabajadas']}"
        assert g_res['estado'] == 'Parcial/Retardo', f"Esperado Parcial/Retardo para Guadalupe, obtenido {g_res['estado']}"
        assert 'Retardo' in g_res['observaciones'], f"Esperada observación de Retardo para Guadalupe, obtenido {g_res['observaciones']}"

        # Aserción para Margarita (ID 12)
        m_res = next(r for r in resultados if r['id_docente'] == 12)
        assert m_res['horas_trabajadas'] == 3.78, f"Esperado 3.78 para Margarita, obtenido {m_res['horas_trabajadas']}"
        assert m_res['estado'] == 'Advertencia', f"Esperado Advertencia para Margarita, obtenido {m_res['estado']}"
        assert 'No registró por hora' in m_res['observaciones'], f"Esperada advertencia de registro por hora para Margarita, obtenido {m_res['observaciones']}"
        assert '12:00' in m_res['observaciones'] and '13:00' in m_res['observaciones'] and '14:00' in m_res['observaciones'], f"Esperadas horas omitidas exactas para Margarita, obtenido {m_res['observaciones']}"

        # Aserción para Karen Itzel (ID 15)
        k_res = next(r for r in resultados if r['id_docente'] == 15)
        assert k_res['horas_trabajadas'] == 2.88, f"Esperado 2.88 para Karen Itzel, obtenido {k_res['horas_trabajadas']}"
        assert k_res['estado'] == 'Parcial/Retardo', f"Esperado Parcial/Retardo para Karen Itzel, obtenido {k_res['estado']}"
        assert 'Retardo' in k_res['observaciones'], f"Esperado Retardo para Karen Itzel, obtenido {k_res['observaciones']}"
        assert 'No registró por hora' not in k_res['observaciones'], f"No esperada advertencia para Karen Itzel, obtenido {k_res['observaciones']}"

        print("\n¡TODAS LAS PRUEBAS DE CASOS COMPLEJOS PASARON CON ÉXITO!")

        # 5. Limpieza
        print("\nLimpiando base de datos...")
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente IN (12, 14, 15)")
            cursor.execute("DELETE FROM tb_horarios WHERE id_grupo = 9999")
            cursor.execute("DELETE FROM tb_materias WHERE id = 9999")
            cursor.execute("DELETE FROM tb_grupos WHERE id = 9999")
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente IN (12, 14, 15)")
            conn.commit()
        print("Limpieza completada.")

    except Exception as e:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente IN (12, 14, 15)")
                cursor.execute("DELETE FROM tb_horarios WHERE id_grupo = 9999")
                cursor.execute("DELETE FROM tb_materias WHERE id = 9999")
                cursor.execute("DELETE FROM tb_grupos WHERE id = 9999")
                cursor.execute("DELETE FROM tb_docentes WHERE idDocente IN (12, 14, 15)")
                conn.commit()
        except:
            pass
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
