from app.config.conexion import get_connection
import pymysql

def check_group_grades():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Get group details
        cursor.execute("SELECT id, clave, id_nivel_academico, id_centroTrabajo FROM tb_grupos WHERE clave = 'BGNE280625S'")
        grupo = cursor.fetchone()
        if not grupo:
            print("Group BGNE280625S not found.")
            return
            
        print(f"Group: {grupo}")
        
        # Get subject details for Individuo y Sociedad
        cursor.execute("SELECT id, nombreMateria, id_nivel_academico FROM tb_materias WHERE nombreMateria LIKE '%individuo%'")
        materias = cursor.fetchall()
        print("\nMaterias for 'individuo':")
        for m in materias:
            print(m)
            
        # Get all calificaciones for this group
        cursor.execute("""
            SELECT c.id, c.idAlumno, a.nombre, a.apPaterno, c.idMateria, m.nombreMateria, c.calificacion 
            FROM tb_calificaciones c
            JOIN tb_alumnos a ON c.idAlumno = a.idAlumno
            JOIN tb_materias m ON c.idMateria = m.id
            WHERE c.idGrupo = %s OR a.idGrupo = %s
        """, (grupo["id"], grupo["id"]))
        califs = cursor.fetchall()
        print(f"\nTotal calificaciones for group: {len(califs)}")
        for c in califs[:20]:
            print(f"Alumno: {c['nombre']} {c['apPaterno']} | Materia: {c['nombreMateria']} (ID: {c['idMateria']}) | Grade: {c['calificacion']}")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_group_grades()
