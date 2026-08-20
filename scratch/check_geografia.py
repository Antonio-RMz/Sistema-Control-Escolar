from app.config.conexion import get_connection
import pymysql

def check_geografia():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id, nombreMateria, id_nivel_academico, idCentroTrabajo, clave FROM tb_materias WHERE nombreMateria LIKE '%geograf%' OR nombreMateria LIKE '%geográf%' OR nombreMateria LIKE '%GEO%'")
        mats = cursor.fetchall()
        print("--- GEOGRAFIA MATERIAS ---")
        for m in mats:
            print(f"ID: {m['id']} | Level: {m['id_nivel_academico']} | CCT: {m['idCentroTrabajo']} | Clave: {m['clave']} | Name: {m['nombreMateria']}")
            
        print("\n--- ALL MATERIAS FOR CCT 3 ---")
        cursor.execute("SELECT id, nombreMateria, id_nivel_academico, idCentroTrabajo, clave FROM tb_materias WHERE idCentroTrabajo = 3")
        all_cct3 = cursor.fetchall()
        for m in all_cct3:
            print(f"ID: {m['id']} | Level: {m['id_nivel_academico']} | Clave: {m['clave']} | Name: {m['nombreMateria']}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_geografia();
