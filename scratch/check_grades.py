from app.config.conexion import get_connection
import pymysql

def check_grades():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Select distinct materias from tb_calificaciones and their levels/CCTs
        cursor.execute("""
            SELECT DISTINCT c.idMateria, m.nombreMateria, m.id_nivel_academico, m.idCentroTrabajo, m.clave
            FROM tb_calificaciones c
            JOIN tb_materias m ON c.idMateria = m.id
        """)
        mats = cursor.fetchall()
        print("--- MATERIAS IN tb_calificaciones ---")
        for m in mats:
            print(f"ID: {m['idMateria']} | Name: {m['nombreMateria']} | Level: {m['id_nivel_academico']} | CCT: {m['idCentroTrabajo']} | Clave: {m['clave']}")
            
        # Select all alumnos
        cursor.execute("SELECT idAlumno, nombre, apPaterno, apMaterno FROM tb_alumnos")
        alumnos = cursor.fetchall()
        print("\n--- ALUMNOS ---")
        for a in alumnos:
            print(f"ID: {a['idAlumno']} | Nombre: {a['nombre']} {a['apPaterno']} {a['apMaterno']}")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_grades()
