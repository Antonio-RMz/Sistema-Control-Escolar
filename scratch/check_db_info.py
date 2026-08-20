from app.config.conexion import get_connection
import pymysql

def check_db():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # CCTs
        cursor.execute("SELECT id, nombre, clave, idTipoPeriodo FROM tb_centrotrabajo")
        ccts = cursor.fetchall()
        print("--- CENTROS DE TRABAJO (CCT) ---")
        for c in ccts:
            print(f"ID: {c['id']} | Nombre: {c['nombre']} | Clave: {c['clave']} | TipoPeriodo: {c['idTipoPeriodo']}")
            
        # Niveles académicos
        cursor.execute("SELECT id, nombre, numero, id_tipoPeriodo, activo FROM tb_niveles_academicos")
        niveles = cursor.fetchall()
        print("\n--- NIVELES ACADEMICOS ---")
        for n in niveles:
            print(f"ID: {n['id']} | Nombre: {n['nombre']} | Numero: {n['numero']} | TipoPeriodo: {n['id_tipoPeriodo']} | Activo: {n['activo']}")
            
        # Tipos periodo
        cursor.execute("SELECT id, nombrePeriodo FROM tb_tipoperiodo")
        tps = cursor.fetchall()
        print("\n--- TIPOS PERIODO ---")
        for tp in tps:
            print(f"ID: {tp['id']} | Nombre: {tp['nombrePeriodo']}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_db()
