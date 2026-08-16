import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="escuelabti_dev"
    )
    cursor = conn.cursor()
    
    print("--- SHOW TABLES ---")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for t in tables:
        if "centro" in t[0].lower() or "cct" in t[0].lower() or "config" in t[0].lower():
            print(t[0])
            
    print("\n--- DETALLES DE CENTROS DE TRABAJO ---")
    # Let's see if we have tb_centros_trabajo or similar
    cursor.execute("SHOW TABLES LIKE '%centro%'")
    rows = cursor.fetchall()
    if rows:
        tbl = rows[0][0]
        cursor.execute(f"DESCRIBE {tbl}")
        cols = cursor.fetchall()
        for col in cols:
            print(col)
            
        cursor.execute(f"SELECT * FROM {tbl} LIMIT 5")
        records = cursor.fetchall()
        print("\nRecords:")
        for r in records:
            print(r)
            
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
