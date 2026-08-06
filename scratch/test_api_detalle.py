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
                VALUES ('DOCENTE_PRUEBA_DETALLE', 'TEST_A', 'TEST_B', 'ACTIVO')
            """)
            id_docente = cursor.lastrowid
            print(f"Docente temporal creado con ID: {id_docente}")

            # 2. Crear un grupo temporal vigente en agosto de 2026
            cursor.execute("""
                INSERT INTO tb_grupos (clave, fechaCreacion, fechaInicio, fechaFin)
                VALUES ('GRP_PRUEB_D', '2026-01-01', '2026-08-01', '2026-08-31')
            """)
            id_grupo = cursor.lastrowid
            print(f"Grupo temporal creado con ID: {id_grupo}")

            # 3. Crear materias temporales
            cursor.execute("""
                INSERT INTO tb_materias (nombreMateria, estatusMateria)
                VALUES ('MATERIA_PRUEBA_D1', 1)
            """)
            id_materia1 = cursor.lastrowid
            cursor.execute("""
                INSERT INTO tb_materias (nombreMateria, estatusMateria)
                VALUES ('MATERIA_PRUEBA_D2', 1)
            """)
            id_materia2 = cursor.lastrowid
            print(f"Materias temporales creadas: {id_materia1}, {id_materia2}")

            # 4. Crear horarios para el docente:
            # - Lunes (diaSemana=1): 09:00:00 a 11:00:00 (Materia 1, Aula A)
            # - Lunes (diaSemana=1): 10:30:00 a 12:30:00 (Materia 2, Aula B)
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 1, '09:00:00', '11:00:00', 'Aula A')
            """, (id_grupo, id_materia1, id_docente))
            cursor.execute("""
                INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula)
                VALUES (%s, %s, %s, 1, '10:30:00', '12:30:00', 'Aula B')
            """, (id_grupo, id_materia2, id_docente))
            
            conn.commit()
            print("Horarios temporales creados exitosamente.")

            # 5. Ejecutar get_detalle_horas_docente para el Lunes: 2026-08-17
            print("\nProbando CatalogosService.get_detalle_horas_docente...")
            reporte = CatalogosService.get_detalle_horas_docente(id_docente, "2026-08-17")
            
            print(f"Reporte del docente de prueba: {reporte}")
            
            # Aserciones
            assert len(reporte) == 2, f"Se esperaban 2 registros, se obtuvieron {len(reporte)}"
            
            # Verificar primer registro
            slot1 = next(r for r in reporte if r['materia'] == 'MATERIA_PRUEBA_D1')
            assert slot1['grupo'] == 'GRP_PRUEB_D'
            assert slot1['aula'] == 'Aula A'
            assert slot1['hora_inicio'] in ('09:00:00', '9:00:00')
            assert slot1['hora_fin'] in ('11:00:00', '11:00:00')
            assert slot1['duracion'] == 2
            
            # Verificar segundo registro
            slot2 = next(r for r in reporte if r['materia'] == 'MATERIA_PRUEBA_D2')
            assert slot2['grupo'] == 'GRP_PRUEB_D'
            assert slot2['aula'] == 'Aula B'
            assert slot2['hora_inicio'] == '10:30:00'
            assert slot2['hora_fin'] == '12:30:00'
            assert slot2['duracion'] == 2

            print("\n¡TODAS LAS ASERCIONES PASARON CON ÉXITO!")

            # 6. Limpieza
            print("\nLimpiando base de datos...")
            cursor.execute("DELETE FROM tb_horarios WHERE id_grupo = %s", (id_grupo,))
            cursor.execute("DELETE FROM tb_materias WHERE id IN (%s, %s)", (id_materia1, id_materia2))
            cursor.execute("DELETE FROM tb_grupos WHERE id = %s", (id_grupo,))
            # Para evitar el error de llave foránea por si hay alguna fila de tb_materiadocente creada por trigger
            cursor.execute("DELETE FROM tb_materiadocente WHERE idDocente = %s", (id_docente,))
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (id_docente,))
            conn.commit()
            print("Limpieza completada con éxito.")

    except Exception as e:
        # En caso de error, intentar limpiar para no dejar datos basura
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tb_horarios WHERE id_materia IN (SELECT id FROM tb_materias WHERE nombreMateria LIKE 'MATERIA_PRUEBA_D%%')")
                cursor.execute("DELETE FROM tb_materias WHERE nombreMateria LIKE 'MATERIA_PRUEBA_D%%'")
                cursor.execute("DELETE FROM tb_grupos WHERE clave = 'GRP_PRUEB_D'")
                cursor.execute("DELETE FROM tb_materiadocente WHERE idDocente IN (SELECT idDocente FROM tb_docentes WHERE nombreDocente = 'DOCENTE_PRUEBA_DETALLE')")
                cursor.execute("DELETE FROM tb_docentes WHERE nombreDocente = 'DOCENTE_PRUEBA_DETALLE'")
                conn.commit()
        except:
            pass
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
