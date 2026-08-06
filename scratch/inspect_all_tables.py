import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

def inspect():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
            for t in tables:
                cursor.execute(f"DESCRIBE {t}")
                cols = cursor.fetchall()
                # Check if any column name has 'real' or 'hora'
                for col in cols:
                    field = col['Field'] if isinstance(col, dict) else col[0]
                    if 'real' in field.lower() or 'hora' in field.lower():
                        print(f"Table {t} has column {field}")
    finally:
        conn.close()

if __name__ == '__main__':
    inspect()
