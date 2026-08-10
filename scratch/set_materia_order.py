from app.config.conexion import get_connection

def set_materia_order():
    con = get_connection()
    cur = con.cursor()
    try:
        # 1. Agregar columna orden a tb_materias si no existe
        cur.execute("SHOW COLUMNS FROM tb_materias LIKE 'orden'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE tb_materias ADD COLUMN orden INT DEFAULT 0 AFTER id_nivel_academico")
            print("Columna orden agregada a tb_materias")

        # 2. Definir el orden exacto de las materias de BGNE según la boleta oficial
        bgne_orden = [
            # 1er Trimestre
            ("MATEMATICAS I", 1, 1),
            ("QUIMICA I", 1, 2),
            ("GEOGRAFIA", 1, 3),
            ("INTRODUCCION C. SOCIALES I", 1, 4),
            ("INFORMATICA I", 1, 5),
            ("LECTURA Y REDACCION I", 1, 6),
            ("INGLES I", 1, 7),

            # 2do Trimestre
            ("MATEMATICAS II", 2, 1),
            ("QUIMICA II", 2, 2),
            ("BIOLOGIA I", 2, 3),
            ("HISTORIA DE MEXICO I", 2, 4),
            ("INFORMATICA II", 2, 5),
            ("LECTURA Y REDACCION II", 2, 6),
            ("INGLES II", 2, 7),

            # 3er Trimestre
            ("MATEMATICAS III", 3, 1),
            ("FISICA I", 3, 2),
            ("METODOLOGIA DE LA INVESTIGACION I", 3, 3),
            ("HISTORIA DE MEXICO II", 3, 4),
            ("BIOLOGIA II", 3, 5),
            ("LITERATURA I", 3, 6),
            ("INGLES III", 3, 7),

            # 4to Trimestre
            ("MATEMATICAS IV", 4, 1),
            ("FISICA II", 4, 2),
            ("ECOLOGIA Y MEDIO AMBIENTE", 4, 3),
            ("ESTRUCTURA SOCIOECONOMICA DE MEXICO", 4, 4),
            ("METODOLOGIA DE LA INVESTIGACION II", 4, 5),
            ("LITERATURA II", 4, 6),
            ("INGLES IV", 4, 7),

            # 5to Trimestre
            ("INFORMATICA III", 5, 1),
            ("INGLES V", 5, 2),
            ("CALCULO DIFERENCIAL", 5, 3),
            ("CONTABILIDAD I", 5, 4),
            ("INDIVIDUO Y SOCIEDAD", 5, 5),
            ("TEMAS SELECTOS DE BIOLOGIA I", 5, 6),

            # 6to Trimestre
            ("FILOSOFIA", 6, 1),
            ("INGLES VI", 6, 2),
            ("CALCULO INTEGRAL", 6, 3),
            ("TEMAS SELECTOS DE BIOLOGIA II", 6, 4),
            ("INFORMATICA IV", 6, 5),
            ("CONTABILIDAD II", 6, 6),
        ]

        for nombre_mat, nivel_id, orden_num in bgne_orden:
            search_pattern = f"%{nombre_mat[:6]}%"
            cur.execute("""
                UPDATE tb_materias 
                SET orden = %s, id_nivel_academico = %s
                WHERE nombreMateria LIKE %s AND (idCentroTrabajo = 3 OR clave LIKE %s)
            """, (orden_num, nivel_id, search_pattern, "BGNE%"))

        # Asegurar orden explicito para calculo y filosofia en 6to
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 1 WHERE nombreMateria LIKE %s", ("%FILOSO%",))
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 2 WHERE nombreMateria LIKE %s AND clave = 'BGNEING5'", ("%INGL%S VI%",))
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 3 WHERE nombreMateria LIKE %s", ("%CALCULO INTEGRAL%",))
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 4 WHERE nombreMateria LIKE %s", ("%TEMAS SELECTOS DE BIOLOGIA II%",))
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 5 WHERE nombreMateria LIKE %s", ("%INFORMATICA IV%",))
        cur.execute("UPDATE tb_materias SET id_nivel_academico = 6, orden = 6 WHERE nombreMateria LIKE %s", ("%CONTABILIDAD II%",))

        con.commit()
        print("Orden oficial de materias actualizado exitosamente")
    except Exception as e:
        print("Error al ordenar materias:", e)
        con.rollback()
    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    set_materia_order()
