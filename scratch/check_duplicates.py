from app.config.conexion import get_connection
import pymysql

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    print("--- DUPLICATE SUBJECT NAMES IN tb_materias ---")
    cursor.execute("""
        SELECT nombreMateria, COUNT(*) as count, GROUP_CONCAT(CONCAT('ID: ', id, ' (Nivel: ', IFNULL(id_nivel_academico, 'NULL'), ', Clave: ', clave, ', CCT: ', IFNULL(idCentroTrabajo, 'NULL'), ')') SEPARATOR ' | ') as details
        FROM tb_materias
        GROUP BY nombreMateria
        HAVING count > 1
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    print(f"Total duplicate names found: {len(rows)}")
    for r in rows:
        print(f"Name: {r['nombreMateria']} | Count: {r['count']} | Details: {r['details']}")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
