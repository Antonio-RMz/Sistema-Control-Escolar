from app.config.conexion import get_connection

def check_groups():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tb_grupos")
        result = cursor.fetchall()
        print("\n--- VOLCADO COMPLETO tb_grupos ---")
        for row in result:
            print(row)
        print("----------------------------------\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_groups()
