from app.config.conexion import get_connection
import pymysql

def check_databases():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SHOW DATABASES")
        dbs = cursor.fetchall()
        print("--- DATABASES IN MYSQL ---")
        for db in dbs:
            print(db)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_databases()
