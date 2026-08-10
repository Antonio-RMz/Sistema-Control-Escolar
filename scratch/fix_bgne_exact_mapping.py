from app.config.conexion import get_connection

def fix_exact_mapping():
    con = get_connection()
    cur = con.cursor()
    try:
        # Mapeo exacto por ID según la boleta oficial de la imagen
        # 1er Trimestre (Nivel 1):
        # 1. MATEMATICAS I (id 8)
        # 2. QUIMICA I (id 11)
        # 3. GEOGRAFIA (id 9)
        # 4. INTRODUCCION A CIENCIAS SOCIALES I (id 12)
        # 5. INFORMATICA I (id 10)
        # 6. LECTURA Y REDACCION I (id 13)
        # 7. INGLES I (id 14)
        
        # 2do Trimestre (Nivel 2):
        # 1. MATEMATICAS II (id 15)
        # 2. QUIMICA II (id 18)
        # 3. BIOLOGIA I (id 16)
        # 4. HISTORIA DE MEXICO I (id 19)
        # 5. INFORMATICA II (id 17)
        # 6. LECTURA Y REDACCION II (id 20)
        # 7. INGLES II (id 21)

        # 3er Trimestre (Nivel 3):
        # 1. MATEMATICAS III (id 22)
        # 2. FISICA I (id 23)
        # 3. METODOLOGIA DE LA INVESTIGACION I (id 24)
        # 4. HISTORIA DE MEXICO II (id 25)
        # 5. BIOLOGIA II (id 26)
        # 6. LITERATURA I (id 27)
        # 7. INGLES III (id 28)

        # 4to Trimestre (Nivel 4):
        # 1. MATEMATICAS IV (id 29)
        # 2. FISICA II (id 32)
        # 3. ECOLOGIA Y MEDIO AMBIENTE (id 30)
        # 4. ESTRUCTURA SOCIOECONOMICA DE MEXICO (id 33)
        # 5. METODOLOGIA DE LA INVESTIGACION II (id 31)
        # 6. LITERATURA II (id 34)
        # 7. INGLES IV (id 35)

        # 5to Trimestre (Nivel 5):
        # 1. INFORMATICA III (id 36)
        # 2. INGLES V (id 39)
        # 3. CALCULO DIFERENCIAL (id 37)
        # 4. CONTABILIDAD I (id 40)
        # 5. INDIVIDUO Y SOCIEDAD (id 38)
        # 6. TEMAS SELECTOS DE BIOLOGIA I (id 41)

        # 6to Trimestre (Nivel 6):
        # 1. FILOSOFIA (id 42)
        # 2. INGLES VI (id 45)
        # 3. CALCULO INTEGRAL (id 43)
        # 4. TEMAS SELECTOS DE BIOLOGIA II (id 46)
        # 5. INFORMATICA IV (id 44)
        # 6. CONTABILIDAD II (id 47)

        exact_map = [
            # Nivel 1
            (8, 1, 1), (11, 1, 2), (9, 1, 3), (12, 1, 4), (10, 1, 5), (13, 1, 6), (14, 1, 7),
            # Nivel 2
            (15, 2, 1), (18, 2, 2), (16, 2, 3), (19, 2, 4), (17, 2, 5), (20, 2, 6), (21, 2, 7),
            # Nivel 3
            (22, 3, 1), (23, 3, 2), (24, 3, 3), (25, 3, 4), (26, 3, 5), (27, 3, 6), (28, 3, 7),
            # Nivel 4
            (29, 4, 1), (32, 4, 2), (30, 4, 3), (33, 4, 4), (31, 4, 5), (34, 4, 6), (35, 4, 7),
            # Nivel 5
            (36, 5, 1), (39, 5, 2), (37, 5, 3), (40, 5, 4), (38, 5, 5), (41, 5, 6),
            # Nivel 6
            (42, 6, 1), (45, 6, 2), (43, 6, 3), (46, 6, 4), (44, 6, 5), (47, 6, 6),
        ]

        for mat_id, nivel_id, orden_num in exact_map:
            cur.execute("""
                UPDATE tb_materias 
                SET id_nivel_academico = %s, orden = %s, idCentroTrabajo = 3
                WHERE id = %s
            """, (nivel_id, orden_num, mat_id))

        con.commit()
        print("Mapeo exacto por ID completado exitosamente.")
    except Exception as e:
        print("Error en mapeo exacto:", e)
        con.rollback()
    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    fix_exact_mapping()
