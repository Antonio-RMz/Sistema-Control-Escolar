from app.config.conexion import get_connection
import pymysql

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

canonical_ids = list(range(8, 48))

try:
    print("--- BGNE GRADES AND SUBJECTS ---")
    cursor.execute("""
        SELECT 
            c.id, c.idAlumno, c.idMateria, c.calificacion,
            m.nombreMateria, m.id_nivel_academico, m.clave, m.idCentroTrabajo,
            g.clave as grupo_clave
        FROM tb_calificaciones c
        JOIN tb_materias m ON c.idMateria = m.id
        LEFT JOIN tb_grupos g ON c.idGrupo = g.id
        WHERE m.idCentroTrabajo = 3 OR m.clave LIKE 'BGNE%'
    """)
    rows = cursor.fetchall()
    print(f"Total BGNE grades: {len(rows)}")
    for r in rows:
        status = "Canonical" if r['idMateria'] in canonical_ids else "NON-CANONICAL / DUPLICATE"
        print(f"Calif ID: {r['id']} | Alumno: {r['idAlumno']} | Materia ID: {r['idMateria']} ({status}) | Name: {r['nombreMateria']} | Nivel: {r['id_nivel_academico']} | Clave: {r['clave']} | Grade: {r['calificacion']}")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
