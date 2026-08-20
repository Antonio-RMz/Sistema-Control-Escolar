from app.config.conexion import get_connection
import pymysql

def list_bgne_mats():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT id, nombreMateria, id_nivel_academico, orden, clave
            FROM tb_materias
            WHERE idCentroTrabajo = 3
            ORDER BY id_nivel_academico, COALESCE(orden, id)
        """)
        mats = cursor.fetchall()
        print("--- BGNE MATERIAS IN DATABASE ---")
        for m in mats:
            print(f"ID: {m['id']} | Level: {m['id_nivel_academico']} | Name: {m['nombreMateria']} | Clave: {m['clave']} | Orden: {m['orden']}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    list_bgne_mats()
