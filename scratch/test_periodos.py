import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection
from app.services.periodos_academico import PeriodoAcademicoService

def run_test():
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Crear un grupo de prueba temporal.
            # Su fechaInicio es el 31 de Mayo de 2025 (hace más de un año).
            # Su fechaFin representa el fin de su ciclo completo (6 trimestres de 13 semanas cada uno = 78 semanas).
            # 78 semanas = 546 días.
            test_start = datetime.date(2025, 5, 31)
            test_fin = test_start + datetime.timedelta(weeks=78)
            
            # Buscamos el nivel 1
            cursor.execute("SELECT id FROM tb_niveles_academicos WHERE id = 1")
            lvl = cursor.fetchone()
            if not lvl:
                print("El nivel con ID 1 no existe en la base de datos. Asegúrate de ejecutar db_setup.py.")
                return
            
            clave = f"T-{int(datetime.datetime.now().timestamp()) % 10000000}"
            cursor.execute("""
                INSERT INTO tb_grupos (clave, fechaCreacion, fechaInicio, fechaFin, id_tipoPeriodo, id_nivel_academico)
                VALUES (%s, %s, %s, %s, 2, %s)
            """, (clave, datetime.date.today(), test_start, test_fin, lvl['id']))
            group_id = cursor.lastrowid
            
            print(f"Grupo de prueba creado: ID={group_id}, Clave={clave}")
            print(f"Fechas estáticas del grupo: Inicio={test_start}, Fin={test_fin}, Nivel en DB actualmente={lvl['id']}")
            conn.commit()

            # 2. Ejecutar el cálculo del nivel actual
            print("\nCalculando nivel académico basado en la fecha actual (hoy)...")
            result = PeriodoAcademicoService.calcularNivelGrupo(group_id)
            print("Resultado del cálculo:")
            print(result)

            # 3. Guardar la actualización en la BD (solo actualiza el id_nivel_academico)
            print("\nActualizando nivel en la base de datos...")
            updated = PeriodoAcademicoService.actualizarNivelGrupo(group_id)
            print(f"¿Actualizado? {updated}")

            # 4. Consultar el estado del grupo en la BD tras la actualización
            cursor.execute("""
                SELECT id, clave, fechaInicio, fechaFin, id_nivel_academico 
                FROM tb_grupos 
                WHERE id = %s
            """, (group_id,))
            updated_group = cursor.fetchone()
            print("\nEstado final del grupo en la base de datos:")
            print(f"  Clave: {updated_group['clave']}")
            print(f"  fechaInicio (estática): {updated_group['fechaInicio']}")
            print(f"  fechaFin (estática): {updated_group['fechaFin']}")
            print(f"  id_nivel_academico (actualizado): {updated_group['id_nivel_academico']}")

            # 5. Limpieza del grupo de prueba
            cursor.execute("DELETE FROM tb_grupos WHERE id = %s", (group_id,))
            conn.commit()
            print("\nGrupo de prueba eliminado correctamente.")

    finally:
        conn.close()

if __name__ == '__main__':
    run_test()
