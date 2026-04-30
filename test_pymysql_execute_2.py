from app.config.conexion import get_connection
import traceback

conn = get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT %s, %s, %s", ("A", "B", "C"))
    print("Normal worked")
except Exception as e:
    print("Normal error:", str(e))

try:
    cursor.execute("SELECT %s, %s", (1, [1, 2]))
    print("List inside tuple worked")
except Exception as e:
    print("List inside tuple error:", str(e))

try:
    cursor.execute("SELECT %s, %s, %s", ("A", "B", ["C"]))
    print("List as 3rd param worked")
except Exception as e:
    print("List as 3rd param error:", str(e))

try:
    cursor.execute("SELECT %s, %s", (1, {"a": 1}))
    print("Dict inside tuple worked")
except Exception as e:
    print("Dict inside tuple error:", str(e))

try:
    cursor.execute("SELECT %s, %s, %s", ("A", "B", {"a": 1}))
    print("Dict as 3rd param worked")
except Exception as e:
    print("Dict as 3rd param error:", type(e).__name__, str(e))
