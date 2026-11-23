"""
Migración: modalidad online de 78 semanas (6 trimestres x 13 semanas).

Se puede ejecutar varias veces: solo crea lo que falta y no borra nada.
    python -I scripts/migrar_online_78_semanas.py           (desde la raíz del proyecto)

Crea:
  tb_online_planes            Plan de estudios online (bloques configurables por plan)
  tb_online_plan_bloques      Trimestre / bloque / semanas (los 3 bloques de un trimestre suman 13)
  tb_online_bloque_cursos     Cursos de Moodle de cada bloque (normalmente 2 por bloque)
  tb_online_curso_materias    Materias que cubre cada curso (un curso puede cubrir 2 materias: cursos fusionados)
  tb_alumno_semanas_online    Una fila por semana pagada del alumno (cola FIFO)
  (El calendario sale de las fechas del grupo BGNE del alumno; ver migrar_online_grupos.py)
Agrega:
  tb_alumnos.semana_inicio_online
  tb_alumno_pagos.semana_desde, tb_alumno_pagos.semana_hasta
Siembra:
  Plan "BGNE Online" con 5 + 4 + 4 semanas por trimestre, tomando materias y cursos de Moodle
  de la distribución que ya existe en tb_materias (mes_bloque / par_materia_orden / id_curso_moodle).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.conexion import get_connection  # noqa: E402

SEMANAS_DEFAULT = {1: 5, 2: 4, 3: 4}

TABLAS = {
    "tb_online_planes": """
        CREATE TABLE tb_online_planes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            descripcion VARCHAR(255) NULL,
            activo TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    "tb_online_plan_bloques": """
        CREATE TABLE tb_online_plan_bloques (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_plan INT NOT NULL,
            trimestre TINYINT NOT NULL COMMENT '1 a 6',
            bloque TINYINT NOT NULL COMMENT '1 a 3',
            semanas TINYINT NOT NULL COMMENT 'Duración del bloque; los 3 bloques del trimestre suman 13',
            UNIQUE KEY uk_plan_trim_bloque (id_plan, trimestre, bloque),
            CONSTRAINT fk_opb_plan FOREIGN KEY (id_plan) REFERENCES tb_online_planes(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    "tb_online_bloque_cursos": """
        CREATE TABLE tb_online_bloque_cursos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_plan_bloque INT NOT NULL,
            orden TINYINT NOT NULL DEFAULT 1,
            nombre VARCHAR(200) NOT NULL,
            moodle_course_id INT NULL COMMENT 'ID del curso en Moodle',
            UNIQUE KEY uk_bloque_orden (id_plan_bloque, orden),
            CONSTRAINT fk_obc_bloque FOREIGN KEY (id_plan_bloque) REFERENCES tb_online_plan_bloques(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    "tb_online_curso_materias": """
        CREATE TABLE tb_online_curso_materias (
            id_bloque_curso INT NOT NULL,
            id_materia INT NOT NULL,
            PRIMARY KEY (id_bloque_curso, id_materia),
            CONSTRAINT fk_ocm_curso FOREIGN KEY (id_bloque_curso) REFERENCES tb_online_bloque_cursos(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    "tb_alumno_semanas_online": """
        CREATE TABLE tb_alumno_semanas_online (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_alumno INT NOT NULL,
            semana_global SMALLINT NOT NULL COMMENT '1 a 78',
            id_pago INT NULL,
            fecha_pago DATE NOT NULL,
            estatus ENUM('EN_ESPERA','HABILITADA') NOT NULL DEFAULT 'EN_ESPERA',
            fecha_habilitada DATETIME NULL,
            fecha_limite DATETIME NULL COMMENT '6 días naturales desde el desbloqueo, 23:59:59',
            fecha_limite_original DATETIME NULL,
            prorroga_por VARCHAR(100) NULL,
            prorroga_fecha DATETIME NULL,
            moodle_sincronizado TINYINT(1) NOT NULL DEFAULT 0,
            moodle_error VARCHAR(255) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_alumno_semana (id_alumno, semana_global),
            KEY idx_estatus (estatus, moodle_sincronizado),
            KEY idx_pago (id_pago)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
}

COLUMNAS = [
    ("tb_alumnos", "semana_inicio_online", "SMALLINT NULL COMMENT 'Semana global (1-78) en la que entra a online'"),
    ("tb_alumno_pagos", "semana_desde", "SMALLINT NULL COMMENT 'Primera semana global cubierta'"),
    ("tb_alumno_pagos", "semana_hasta", "SMALLINT NULL COMMENT 'Última semana global cubierta'"),
]


def existe_tabla(cur, tabla):
    cur.execute("SHOW TABLES LIKE %s", (tabla,))
    return cur.fetchone() is not None


def existe_columna(cur, tabla, columna):
    cur.execute(f"SHOW COLUMNS FROM `{tabla}` LIKE %s", (columna,))
    return cur.fetchone() is not None


def sembrar_plan(cur):
    cur.execute("SELECT id FROM tb_online_planes LIMIT 1")
    if cur.fetchone():
        print("  plan: ya existe, no se siembra")
        return

    cur.execute("INSERT INTO tb_online_planes (nombre, descripcion) VALUES (%s, %s)",
                ("BGNE Online", "6 trimestres de 13 semanas (78 semanas). Bloques 5 + 4 + 4."))
    id_plan = cur.lastrowid

    cur.execute("""
        SELECT id, nombreMateria, id_nivel_academico, mes_bloque, COALESCE(par_materia_orden, 1) AS orden, id_curso_moodle
        FROM tb_materias
        WHERE idCentroTrabajo = 3 AND id_nivel_academico BETWEEN 1 AND 6 AND mes_bloque BETWEEN 1 AND 3
        ORDER BY id_nivel_academico, mes_bloque, par_materia_orden, id
    """)
    materias = cur.fetchall()

    # Geografía (9) e Introducción a las Ciencias Sociales I (12) comparten curso en Moodle
    # (12 quedó sin mes_bloque en la distribución anterior).
    cur.execute("SELECT id, nombreMateria, id_nivel_academico, id_curso_moodle FROM tb_materias WHERE id = 12 AND mes_bloque IS NULL")
    intro = cur.fetchone()
    if intro:
        materias.append({**intro, "mes_bloque": 1, "orden": 2})

    for t in range(1, 7):
        for b in range(1, 4):
            cur.execute("INSERT INTO tb_online_plan_bloques (id_plan, trimestre, bloque, semanas) VALUES (%s, %s, %s, %s)",
                        (id_plan, t, b, SEMANAS_DEFAULT[b]))
            id_bloque = cur.lastrowid
            del_bloque = [m for m in materias if int(m["id_nivel_academico"]) == t and int(m["mes_bloque"]) == b]
            for orden in sorted({int(m["orden"]) for m in del_bloque}):
                grupo = [m for m in del_bloque if int(m["orden"]) == orden]
                nombre = " / ".join(m["nombreMateria"].strip() for m in grupo)
                cursos = {int(m["id_curso_moodle"]) for m in grupo if m.get("id_curso_moodle") and int(m["id_curso_moodle"]) > 1}
                course_id = cursos.pop() if len(cursos) == 1 else None
                cur.execute("INSERT INTO tb_online_bloque_cursos (id_plan_bloque, orden, nombre, moodle_course_id) VALUES (%s, %s, %s, %s)",
                            (id_bloque, orden, nombre[:200], course_id))
                id_curso = cur.lastrowid
                for m in grupo:
                    cur.execute("INSERT IGNORE INTO tb_online_curso_materias (id_bloque_curso, id_materia) VALUES (%s, %s)",
                                (id_curso, m["id"]))
    print(f"  plan: sembrado 'BGNE Online' (id {id_plan}) con 18 bloques")


def main():
    con = get_connection()
    cur = con.cursor()
    try:
        for tabla, ddl in TABLAS.items():
            if existe_tabla(cur, tabla):
                print(f"  {tabla}: ya existe")
            else:
                cur.execute(ddl)
                print(f"  {tabla}: creada")
        for tabla, columna, definicion in COLUMNAS:
            if existe_columna(cur, tabla, columna):
                print(f"  {tabla}.{columna}: ya existe")
            else:
                cur.execute(f"ALTER TABLE `{tabla}` ADD COLUMN `{columna}` {definicion}")
                print(f"  {tabla}.{columna}: agregada")
        sembrar_plan(cur)
        con.commit()
        print("Migración completa.")
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    main()
