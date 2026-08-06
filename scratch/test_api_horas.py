import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection
from app.services.catalogos_service import CatalogosService

def run_test():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Crear un docente temporal activo
            cursor.execute("""
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, statusDocente)
                VALUES ('DOCENTE_PRUEBA_HORAS', 'TEST_A', 'TEST_B', 'ACTIVO')
            """)
            id_docente = cursor.lastrowid
            print(f"Docente temporal creado con ID: {id_docente}")

            # 2. Crear un grupo temporal vigente en agosto de 2026
            cursor.execute("""
                INSERT INTO tb_grupos (clave, fechaCreacion, fechaInicio, fechaFin)
                VALUES ('GRP_PRUEB_H', '2026-01-01', '2026-08-01', '2026-08-31')
            """)
            id_grupo = cursor.lastrowid
            print(f"Grupo temporal creado con ID: {id_grupo}")

            # 3. Crear materias temporales
            cursor.execute("""
                INSERT INTO tb_materias (nombreMateria, estatusMateria)
                VALUES ('MATERIA_PRUEBA_H1', 1)
            """)
            id_materia = cursor.lastrowid
            cursor.execute("""
                INSERT INTO tb_materias (nombreMateria, estatusMateria)
                VALUES ('MATERIA_PRUEBA_H2', 1)
            """)
            id_materia2 = cursor.lastrowid
            print(f"Materias temporales creadas: {id_materia}, {id_materia2}")

            # 4. Crear horarios para el docente:
            # - Lunes (diaSemana=1): 09:00:00 a 11:00:00 (2 horas)
            # - Lunes (diaSemana=1): 10:30:00 a 12:30:00 (2 horas) -> Total = 4.0, Real = 3.5 (09:00 a 12:30)
            # - Martes (diaSemana=2): 14:00:00 a 18:00:00 (4 horas, Materia 1)
            # - Martes (diaSemana=2): 14:00:00 a 18:00:00 (4 horas, Materia 2) -> Total = 4, Real = 4 (no se duplica por materia)
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 1, '09:00:00', '11:00:00', 'Aula A')
            """, (id_grupo, id_materia, id_docente))
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 1, '10:30:00', '12:30:00', 'Aula B')
            """, (id_grupo, id_materia, id_docente))
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 2, '14:00:00', '18:00:00', 'Aula C')
            """, (id_grupo, id_materia, id_docente))
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 2, '14:00:00', '18:00:00', 'Aula C')
            """, (id_grupo, id_materia2, id_docente))
            
            conn.commit()
            print("Horarios temporales creados exitosamente.")

            # 5. Ejecutar get_horas_docentes para el rango: 2026-08-16 (Domingo) a 2026-08-18 (Martes)
            print("\nProbando CatalogosService.get_horas_docentes...")
            reporte = CatalogosService.get_horas_docentes("2026-08-16", "2026-08-18")
            
            # Buscar nuestro docente en el reporte
            doc_reporte = next((d for d in reporte if d['id_docente'] == id_docente), None)
            
            if not doc_reporte:
                print("ERROR: No se encontró el docente de prueba en el reporte.")
                sys.exit(1)
            
            print(f"Reporte del docente de prueba: {doc_reporte}")
            
            # Aserciones
            dias = doc_reporte['dias']
            assert len(dias) == 3, f"Se esperaban 3 días, se obtuvieron {len(dias)}"
            
            # 2026-08-16 (Domingo) -> 0 horas
            domingo = next(d for d in dias if d['fecha'] == '2026-08-16')
            assert domingo['total'] == 0, f"Domingo total esperado 0, obtenido {domingo['total']}"
            assert domingo['real'] == 0, f"Domingo real esperado 0, obtenido {domingo['real']}"
            
            # 2026-08-17 (Lunes) -> Total: 4.0, Real: 3.5 (distintos bloques)
            lunes = next(d for d in dias if d['fecha'] == '2026-08-17')
            assert lunes['total'] == 4.0, f"Lunes total esperado 4.0, obtenido {lunes['total']}"
            assert lunes['real'] == 3.5, f"Lunes real esperado 3.5, obtenido {lunes['real']}"
            
            # 2026-08-18 (Martes) -> Total: 4, Real: 4 (se deduplicó la hora idéntica de las dos materias)
            martes = next(d for d in dias if d['fecha'] == '2026-08-18')
            assert martes['total'] == 4, f"Martes total esperado 4, obtenido {martes['total']}"
            assert martes['real'] == 4, f"Martes real esperado 4, obtenido {martes['real']}"
            
            print("\n¡TODAS LAS ASERCIONES PASARON CON ÉXITO!")

            # 6. Limpieza
            print("\nLimpiando base de datos...")
            cursor.execute("DELETE FROM tb_horarios WHERE id_grupo = %s", (id_grupo,))
            cursor.execute("DELETE FROM tb_materias WHERE id IN (%s, %s)", (id_materia, id_materia2))
            cursor.execute("DELETE FROM tb_grupos WHERE id = %s", (id_grupo,))
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (id_docente,))
            conn.commit()
            print("Limpieza completada.")

    except Exception as e:
        # En caso de error, intentar limpiar para no dejar datos basura
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tb_horarios WHERE id_materia IN (SELECT id FROM tb_materias WHERE nombreMateria LIKE 'MATERIA_PRUEBA_H%%')")
                cursor.execute("DELETE FROM tb_materias WHERE nombreMateria LIKE 'MATERIA_PRUEBA_H%%'")
                cursor.execute("DELETE FROM tb_grupos WHERE clave = 'GRP_PRUEB_H'")
                cursor.execute("DELETE FROM tb_docentes WHERE nombreDocente = 'DOCENTE_PRUEBA_HORAS'")
                conn.commit()
        except:
            pass
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
