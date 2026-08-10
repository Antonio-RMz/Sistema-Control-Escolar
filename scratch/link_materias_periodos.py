from app.config.conexion import get_connection

def update_materias():
    con = get_connection()
    cur = con.cursor()
    try:
        mapping_bgne = {
            1: [8, 9, 10, 11, 12, 13, 14], # 1er Trimestre
            2: [15, 16, 17, 18, 19, 20, 21], # 2do Trimestre
            3: [22, 23, 24, 25, 26, 27, 28], # 3er Trimestre
            4: [29, 30, 31, 32, 33, 34, 35], # 4to Trimestre
            5: [36, 37, 38, 39, 40, 41],     # 5to Trimestre
            6: [42, 43, 44, 45, 46, 47]      # 6to Trimestre
        }
        for nivel_id, mat_ids in mapping_bgne.items():
            placeholders = ','.join(['%s'] * len(mat_ids))
            cur.execute(f"UPDATE tb_materias SET id_nivel_academico = %s, idCentroTrabajo = 3 WHERE id IN ({placeholders})", [nivel_id] + mat_ids)
        print("Materias de BGNE vinculadas con sus respectivos trimestres 1 a 6 y CCT=3")

        # Vincular CCT de BTI
        cur.execute("UPDATE tb_materias SET idCentroTrabajo = 2 WHERE clave LIKE 'BTI%' OR clave LIKE '%-BTI%' OR idCentroTrabajo IS NULL")
        print("Materias restantes asignadas a BTI")

        con.commit()
    except Exception as e:
        print("Error vinculando materias:", e)
        con.rollback()
    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    update_materias()
