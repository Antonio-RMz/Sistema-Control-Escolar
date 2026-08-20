from app.config.conexion import get_connection
import pymysql

def check_calif():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT c.id, c.idAlumno, c.idMateria, m.nombreMateria, c.id_nivel_academico as calif_lvl, m.id_nivel_academico as mat_lvl, c.calificacion, c.tipoAcreditacion, c.idGrupo
            FROM tb_calificaciones c
            JOIN tb_materias m ON c.idMateria = m.id
            WHERE c.idAlumno = 6
        """)
        rows = cursor.fetchall()
        print("--- CALIFICACIONES FOR ALUMNO 6 ---")
        for r in rows:
            print(f"ID: {r['id']} | MateriaID: {r['idMateria']} | Name: {r['nombreMateria']} | CalifLvl: {r['calif_lvl']} | MatLvl: {r['mat_lvl']} | Calif: {r['calificacion']} | Tipo: {r['tipoAcreditacion']} | Grupo: {r['idGrupo']}")
            
        cursor.execute("SELECT id, clave, id_nivel_academico, id_centroTrabajo FROM tb_grupos WHERE id IN (SELECT DISTINCT idGrupo FROM tb_calificaciones WHERE idAlumno = 6)")
        grupos = cursor.fetchall()
        print("\n--- GRUPOS ASSOCIATED WITH ALUMNO 6 GRADES ---")
        for g in grupos:
            print(f"ID: {g['id']} | Clave: {g['clave']} | Level: {g['id_nivel_academico']} | CCT: {g['id_centroTrabajo']}")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_calif()
