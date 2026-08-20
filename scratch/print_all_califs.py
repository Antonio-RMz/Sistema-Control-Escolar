from app.config.conexion import get_connection
import pymysql

def print_all_califs():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.idAlumno, a.nombre, a.apPaterno, c.idMateria, m.nombreMateria, c.calificacion, c.idGrupo
            FROM tb_calificaciones c
            JOIN tb_alumnos a ON c.idAlumno = a.idAlumno
            JOIN tb_materias m ON c.idMateria = m.id
        """)
        rows = cursor.fetchall()
        print("--- ALL CALIFICACIONES IN DB ---")
        for r in rows:
            print(f"ID: {r['id']} | Alumno: {r['idAlumno']} ({r['nombre']} {r['apPaterno']}) | Materia: {r['idMateria']} ({r['nombreMateria']}) | Calif: {r['calificacion']} | Grupo: {r['idGrupo']}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print_all_califs()
