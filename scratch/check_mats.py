from app.config.conexion import get_connection
import pymysql

def check_mats():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Show columns of tb_materias
        cursor.execute("DESCRIBE tb_materias")
        columns = cursor.fetchall()
        print("--- COLUMNS OF tb_materias ---")
        for col in columns:
            print(f"Field: {col['Field']} | Type: {col['Type']}")
            
        # Get count of materias per CCT and level
        cursor.execute("""
            SELECT idCentroTrabajo, id_nivel_academico, COUNT(*) as cnt 
            FROM tb_materias 
            GROUP BY idCentroTrabajo, id_nivel_academico
        """)
        counts = cursor.fetchall()
        print("\n--- MATERIAS COUNT ---")
        for c in counts:
            print(f"CCT: {c['idCentroTrabajo']} | Level: {c['id_nivel_academico']} | Count: {c['cnt']}")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_mats()
