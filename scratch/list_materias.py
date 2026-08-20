from app.config.conexion import get_connection
import pymysql

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    print("--- ALL SUBJECTS (tb_materias) ---")
    cursor.execute("""
        SELECT m.id, m.nombreMateria, m.clave, m.id_nivel_academico, m.idCentroTrabajo, m.orden 
        FROM tb_materias m
        ORDER BY m.nombreMateria, m.id_nivel_academico
    """)
    rows = cursor.fetchall()
    print(f"Total subjects found: {len(rows)}")
    for r in rows:
        print(f"ID: {r['id']} | Name: {r['nombreMateria']} | Clave: {r['clave']} | Nivel: {r['id_nivel_academico']} | CCT: {r['idCentroTrabajo']} | Orden: {r['orden']}")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
