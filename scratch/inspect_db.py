from app.config.conexion import get_connection
import pymysql

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    print("--- HORARIOS BGNE ---")
    query = """
        SELECT 
            h.id_horario,
            h.id_grupo,
            g.clave AS grupo_clave,
            h.diaSemana,
            h.horaInicio,
            h.horaFin,
            h.aula,
            m.nombreMateria,
            d.nombreDocente,
            d.apPaternoDocente
        FROM tb_horarios h
        JOIN tb_grupos g ON h.id_grupo = g.id
        JOIN tb_materias m ON h.id_materia = m.id
        JOIN tb_docentes d ON h.id_docente = d.idDocente
        WHERE g.id_centroTrabajo = 3
        ORDER BY h.diaSemana, h.horaInicio
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Total BGNE schedules found: {len(rows)}")
    for r in rows:
        r['horaInicio'] = str(r['horaInicio'])
        r['horaFin'] = str(r['horaFin'])
        print(r)
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
