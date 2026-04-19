from app.config.conexion import get_connection
import sys

def test_insert(id_gen):
    conn = get_connection()
    cur = conn.cursor()
    try:
        print(f"Testing insert with id_gen={id_gen}")
        cur.execute("SELECT id FROM tb_generaciones WHERE id=%s", (id_gen,))
        row = cur.fetchone()
        if not row:
            print(f"Error: Generation ID {id_gen} NOT found in tb_generaciones")
            return
        
        print(f"Found generation: {row}")
        
        query = "INSERT INTO tb_alumnos (nombre, apPaterno, idGeneracion) VALUES ('TEST', 'TEST', %s)"
        cur.execute(query, (id_gen,))
        conn.commit()
        print("Insert SUCCESSFUL")
        
        cur.execute("DELETE FROM tb_alumnos WHERE nombre='TEST'")
        conn.commit()
        print("Cleaned up.")
        
    except Exception as e:
        print(f"Caught error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_id = 39
    if len(sys.argv) > 1:
        test_id = int(sys.argv[1])
    test_insert(test_id)
