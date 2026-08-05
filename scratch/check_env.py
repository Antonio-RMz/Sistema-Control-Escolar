import os
from dotenv import load_dotenv
from app.config.conexion import get_connection

load_dotenv()

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SHOW INDEX FROM tb_grupos")
    indexes = cur.fetchall()
    print("\n--- ÍNDICES EN tb_grupos ---")
    for idx in indexes:
        print(f"Key_name: {idx['Key_name']} | Column_name: {idx['Column_name']} | Non_unique: {idx['Non_unique']}")
    print("----------------------------\n")
except Exception as e:
    print("Error:", e)
