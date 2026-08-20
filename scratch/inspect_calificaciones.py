from app.config.conexion import get_connection
import pymysql

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    print("--- CALIFICACIONES REGISTRADAS (tb_calificaciones) ---")
    cursor.execute("""
        SELECT 
            c.id, c.idAlumno, c.idMateria, c.id_nivel_academico AS calif_nivel, c.idGrupo,
            m.nombreMateria, m.id_nivel_academico AS materia_nivel,
            g.clave AS grupo_clave, g.id_nivel_academico AS grupo_nivel
        FROM tb_calificaciones c
        JOIN tb_materias m ON c.idMateria = m.id
        LEFT JOIN tb_grupos g ON c.idGrupo = g.id
        LIMIT 100
    """)
    rows = cursor.fetchall()
    print(f"Total rows found: {len(rows)}")
    for r in rows:
        print(f"ID: {r['id']} | Alumno: {r['idAlumno']} | Materia: {r['nombreMateria']} (ID: {r['idMateria']}, Nivel: {r['materia_nivel']}) | Calif Nivel: {r['calif_nivel']} | Grupo: {r['grupo_clave']} (Nivel: {r['grupo_nivel']})")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
