from app.config.conexion import get_connection

conn = get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT %s, %s", (1, [1, 2]))
    print("List worked")
except Exception as e:
    print("List error:", str(e))

try:
    cursor.execute("SELECT %s, %s", (1, {"a": 1}))
    print("Dict worked")
except Exception as e:
    print("Dict error:", str(e))
