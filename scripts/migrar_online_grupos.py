"""
Migración: el calendario online sale del GRUPO del alumno (BGNE), no de una cohorte.

Se puede ejecutar varias veces.
    python scripts/migrar_online_grupos.py

- Elimina tb_online_cohortes y tb_alumnos.id_cohorte_online (creadas por migrar_online_78_semanas.py; se verifica que
  no tengan datos antes de borrarlas).
- Agrega tb_grupos.id_plan_online (opcional): plan de bloques online del grupo. Sin valor se usa el plan base.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.conexion import get_connection  # noqa: E402


def existe_tabla(cur, tabla):
    cur.execute("SHOW TABLES LIKE %s", (tabla,))
    return cur.fetchone() is not None


def existe_columna(cur, tabla, columna):
    cur.execute(f"SHOW COLUMNS FROM `{tabla}` LIKE %s", (columna,))
    return cur.fetchone() is not None


def main():
    con = get_connection()
    cur = con.cursor()
    try:
        if existe_columna(cur, "tb_alumnos", "id_cohorte_online"):
            cur.execute("SELECT COUNT(*) AS n FROM tb_alumnos WHERE id_cohorte_online IS NOT NULL")
            if cur.fetchone()["n"]:
                raise SystemExit("tb_alumnos.id_cohorte_online tiene datos; no se elimina.")
            cur.execute("ALTER TABLE tb_alumnos DROP COLUMN id_cohorte_online")
            print("  tb_alumnos.id_cohorte_online: eliminada")
        if existe_tabla(cur, "tb_online_cohortes"):
            cur.execute("SELECT COUNT(*) AS n FROM tb_online_cohortes")
            if cur.fetchone()["n"]:
                raise SystemExit("tb_online_cohortes tiene datos; no se elimina.")
            cur.execute("DROP TABLE tb_online_cohortes")
            print("  tb_online_cohortes: eliminada")
        if not existe_columna(cur, "tb_grupos", "id_plan_online"):
            cur.execute("ALTER TABLE tb_grupos ADD COLUMN id_plan_online INT NULL COMMENT 'Plan de bloques online (BGNE). NULL = plan base'")
            print("  tb_grupos.id_plan_online: agregada")
        else:
            print("  tb_grupos.id_plan_online: ya existe")
        con.commit()
        print("Migración completa.")
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    main()
