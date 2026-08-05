import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection
from app.services.alumnos_service import AlumnosService

def run_test():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Crear un alumno de prueba y un grupo de prueba
            cursor.execute("SELECT id FROM tb_grupos LIMIT 1")
            grupo = cursor.fetchone()
            if not grupo:
                print("No hay grupos para la prueba.")
                return
            id_grupo = grupo['id']

            # Insertar alumno temporal sin grupo inicialmente
            cursor.execute("""
                INSERT INTO tb_alumnos (nombre, apPaterno, apMaterno)
                VALUES ('Alumno', 'Test', 'Update')
            """)
            id_alumno = cursor.lastrowid
            conn.commit()
            print(f"Creado alumno temporal ID={id_alumno}")

            # 2. Consultar tb_alumnoGrupo (debería estar vacía para este alumno)
            cursor.execute("SELECT * FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))
            rel1 = cursor.fetchone()
            print(f"Relación inicial en tb_alumnoGrupo (esperado None): {rel1}")

            # 3. Actualizar el alumno asignándole el grupo
            data_update = {
                "nombre": "Alumno",
                "apPaterno": "Test",
                "apMaterno": "Update",
                "idGrupo": id_grupo
            }
            res_update = AlumnosService.update_alumno(id_alumno, data_update)
            print(f"Resultado de asignación de grupo: {res_update}")

            # 4. Verificar que se insertó la relación en tb_alumnoGrupo
            conn.commit() # Reiniciar transacción para ver cambios de otra conexión
            cursor.execute("SELECT * FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))
            rel2 = cursor.fetchone()
            print(f"Relación después de asignación: {rel2}")

            # 5. Actualizar el alumno quitándole el grupo
            data_remove = {
                "nombre": "Alumno",
                "apPaterno": "Test",
                "apMaterno": "Update",
                "idGrupo": None
            }
            res_remove = AlumnosService.update_alumno(id_alumno, data_remove)
            print(f"Resultado de remoción de grupo: {res_remove}")

            # 6. Verificar que se eliminó la relación en tb_alumnoGrupo
            conn.commit() # Reiniciar transacción para ver cambios de otra conexión
            cursor.execute("SELECT * FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))
            rel3 = cursor.fetchone()
            print(f"Relación después de remoción (esperado None): {rel3}")

            # 7. Limpieza final
            cursor.execute("DELETE FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))
            conn.commit()
            print("Limpieza completada.")

    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
