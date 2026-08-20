from app.config.conexion import get_connection
import pymysql

def count_all_califs():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM tb_calificaciones")
        print(f"Total rows in tb_calificaciones: {cursor.fetchone()['cnt']}")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM tb_alumnos")
        print(f"Total rows in tb_alumnos: {cursor.fetchone()['cnt']}")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM tb_materias")
        print(f"Total rows in tb_materias: {cursor.fetchone()['cnt']}")
        
        # Check students in group 4
        cursor.execute("SELECT COUNT(*) as cnt FROM tb_alumnos WHERE idGrupo = 4")
        print(f"Students in group 4: {cursor.fetchone()['cnt']}")
        
        # Check if there are any qualifications for students in group 4
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM tb_calificaciones c
            JOIN tb_alumnos a ON c.idAlumno = a.idAlumno
            WHERE a.idGrupo = 4
        """)
        print(f"Qualifications for students in group 4: {cursor.fetchone()['cnt']}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    count_all_califs()
