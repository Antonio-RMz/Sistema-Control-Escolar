from app.config.conexion import get_connection
import pymysql

def check_tables():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("--- TABLES IN DATABASE ---")
        for t in tables:
            print(list(t.values())[0])
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_tables()
