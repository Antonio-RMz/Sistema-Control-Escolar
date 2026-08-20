from app.config.conexion import get_connection
import pymysql
from scratch.test_kardex_logic import normalize_subject_name

def find_duplicates():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id, nombreMateria, id_nivel_academico, idCentroTrabajo FROM tb_materias")
        mats = cursor.fetchall()
        print("--- DUPLICATE MATERIAS BY NORMALIZED NAME ---")
        by_name = {}
        for m in mats:
            norm = normalize_subject_name(m['nombreMateria'])
            by_name.setdefault(norm, []).append(m)
            
        for norm, list_m in by_name.items():
            if len(list_m) > 1:
                print(f"Normalized Name: {norm}")
                for m in list_m:
                    print(f"  ID: {m['id']} | Level: {m['id_nivel_academico']} | CCT: {m['idCentroTrabajo']} | Original Name: {m['nombreMateria']}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    find_duplicates()
