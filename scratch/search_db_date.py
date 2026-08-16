import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymysql
from app.config.conexion import get_connection

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for row in tables:
        table_name = list(row.values())[0]
        cursor.execute(f"DESCRIBE {table_name}")
        cols = cursor.fetchall()
        for col in cols:
            col_name = col['Field']
            col_type = col['Type']
            if any(t in col_type.lower() for t in ['date', 'time', 'char', 'text', 'varchar']):
                try:
                    cursor.execute(f"SELECT * FROM {table_name} WHERE `{col_name}` LIKE '%2026-08-24%'")
                    results = cursor.fetchall()
                    if results:
                        print(f"Found in table: {table_name}, column: {col_name}")
                        print(results)
                except Exception as ex:
                    pass
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
