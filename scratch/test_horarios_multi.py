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
            # 1. Obtener datos o crear temporales si no existen
            cursor.execute("SELECT id FROM tb_grupos LIMIT 1")
            group = cursor.fetchone()
            if not group:
                print("Creando grupo temporal...")
                cursor.execute("INSERT INTO tb_grupos (clave, fechaCreacion, fechaInicio, fechaFin) VALUES ('T-GRP-1', '2026-01-01', '2026-01-01', '2026-12-31')")
                id_grupo = cursor.lastrowid
                conn.commit()
                created_group = True
            else:
                id_grupo = group['id']
                created_group = False

            cursor.execute("SELECT id FROM tb_materias LIMIT 2")
            materias = cursor.fetchall()
            created_materias = []
            if len(materias) < 2:
                print("Creando materias temporales...")
                for i in range(2 - len(materias)):
                    cursor.execute("INSERT INTO tb_materias (nombreMateria, descripcionMateria, estatusMateria) VALUES (%s, 'Test', 1)", (f"Materia Test {i+1}",))
                    created_materias.append(cursor.lastrowid)
                conn.commit()
                # Volver a cargar materias
                cursor.execute("SELECT id FROM tb_materias LIMIT 2")
                materias = cursor.fetchall()

            cursor.execute("SELECT idDocente FROM tb_docentes LIMIT 2")
            docentes = cursor.fetchall()
            created_docentes = []
            if len(docentes) < 1:
                print("Creando docente temporal...")
                cursor.execute("""
                    INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, statusDocente)
                    VALUES ('Docente Test', 'Test', 'Test', 'test@test.com', 1)
                """)
                created_docentes.append(cursor.lastrowid)
                conn.commit()
                # Volver a cargar docentes
                cursor.execute("SELECT idDocente FROM tb_docentes LIMIT 2")
                docentes = cursor.fetchall()

            mat1_id = materias[0]['id']
            mat2_id = materias[1]['id']
            doc1_id = docentes[0]['idDocente']

            print(f"Usando Grupo ID={id_grupo}")
            print(f"Materia 1: {mat1_id}, Materia 2: {mat2_id}")
            print(f"Docente: {doc1_id}")

            # 2. Probar creación de horarios múltiples en un mismo bloque (un solo docente, múltiples materias)
            payload = {
                "id_grupo": id_grupo,
                "diaSemana": 2, # Martes
                "horaInicio": "15:00:00",
                "horaFin": "16:00:00",
                "id_docente": doc1_id,
                "materias": [mat1_id, mat2_id]
            }

            print("\nCreando horario con múltiples materias y un único docente...")
            res_create = CatalogosService.create_horario_grupo(payload)
            print("Resultado creación:", res_create)

            # 3. Probar consulta plana (agrupado=False)
            print("\nConsultando horario (formato plano, agrupado=False):")
            res_flat = CatalogosService.getHorariosGrupo(id_grupo, agrupado=False)
            test_slots = [h for h in res_flat if h["diaSemana"] == 2 and str(h["horaInicio"]) == "15:00:00"]
            print(f"Encontradas {len(test_slots)} filas en el bloque de las 15:00:")
            for slot in test_slots:
                print(slot)

            # 4. Probar consulta agrupada (agrupado=True)
            print("\nConsultando horario (formato agrupado, agrupado=True):")
            res_grouped = CatalogosService.getHorariosGrupo(id_grupo, agrupado=True)
            test_grouped_slots = [h for h in res_grouped if h["diaSemana"] == 2 and str(h["horaInicio"]) == "15:00:00"]
            print("Bloque de las 15:00 agrupado:")
            for slot in test_grouped_slots:
                print(slot)

            # 5. Limpieza
            print("\nEliminando los registros creados para la prueba...")
            cursor.execute("""
                DELETE FROM tb_horarios 
                WHERE id_grupo = %s AND diaSemana = 2 AND horaInicio = '15:00:00'
            """, (id_grupo,))
            
            # Limpiar grupos creados
            if created_group:
                cursor.execute("DELETE FROM tb_grupos WHERE id = %s", (id_grupo,))
                print("Grupo temporal eliminado.")

            # Limpiar materias creadas
            for mid in created_materias:
                cursor.execute("DELETE FROM tb_materias WHERE id = %s", (mid,))
                print(f"Materia temporal {mid} eliminada.")

            # Limpiar docentes creados
            for did in created_docentes:
                cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (did,))
                print(f"Docente temporal {did} eliminado.")

            conn.commit()
            print("Limpieza completada.")

    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
