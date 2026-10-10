import math
from datetime import date, datetime
from app.config.conexion import get_connection

class ReportesIndisciplinaService:

    @staticmethod
    def _asegurar_tabla(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `tb_reportes_indisciplina` (
              `id` bigint unsigned NOT NULL AUTO_INCREMENT,
              `folio` varchar(255) NOT NULL,
              `id_alumno` int NOT NULL,
              `alumno_nombre` varchar(255) NOT NULL,
              `tutor_nombre` varchar(255) DEFAULT NULL,
              `fecha` date NOT NULL,
              `incidente` text NOT NULL,
              `parcial` int NOT NULL,
              `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `tb_reportes_indisciplina_folio_unique` (`folio`),
              KEY `tb_reportes_indisciplina_id_alumno_index` (`id_alumno`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

    @staticmethod
    def _serializar_fechas(registro):
        if not registro:
            return registro
        for k, v in registro.items():
            if isinstance(v, (date, datetime)):
                registro[k] = str(v)
        return registro

    @staticmethod
    def listar_reportes(id_alumno=None, search=None, page=1, limit=15):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ReportesIndisciplinaService._asegurar_tabla(cursor)

            page = max(1, int(page)) if page else 1
            limit = max(1, int(limit)) if limit else 15
            offset = (page - 1) * limit

            where_clauses = []
            params = []

            if id_alumno:
                where_clauses.append("id_alumno = %s")
                params.append(int(id_alumno))

            if search and str(search).strip():
                s = f"%{str(search).strip()}%"
                where_clauses.append("(folio LIKE %s OR alumno_nombre LIKE %s OR tutor_nombre LIKE %s OR incidente LIKE %s)")
                params.extend([s, s, s, s])

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            # Conteo total
            count_query = f"SELECT COUNT(*) as total FROM tb_reportes_indisciplina {where_sql}"
            cursor.execute(count_query, params)
            total_row = cursor.fetchone()
            total = total_row['total'] if isinstance(total_row, dict) else (total_row[0] if total_row else 0)

            # Registros paginados
            query = f"""
                SELECT id, folio, id_alumno, alumno_nombre, tutor_nombre, fecha, incidente, parcial, created_at, updated_at
                FROM tb_reportes_indisciplina
                {where_sql}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall() or []
            data = [ReportesIndisciplinaService._serializar_fechas(r) for r in rows]

            last_page = max(1, math.ceil(total / limit)) if total > 0 else 1

            return {
                "success": True,
                "data": data,
                "total": total,
                "current_page": page,
                "last_page": last_page
            }
        finally:
            conexion.close()

    @staticmethod
    def crear_reporte(data):
        id_alumno = data.get('id_alumno')
        alumno_nombre = data.get('alumno_nombre')
        incidente = data.get('incidente')
        parcial = data.get('parcial')
        tutor_nombre = data.get('tutor_nombre') or 'S/N'

        # Validaciones
        if not id_alumno or not alumno_nombre or not incidente or parcial is None:
            return {
                "success": False,
                "message": "Datos inválidos. Se requiere id_alumno, alumno_nombre, incidente y parcial.",
                "errors": {
                    "id_alumno": ["Requerido"] if not id_alumno else [],
                    "alumno_nombre": ["Requerido"] if not alumno_nombre else [],
                    "incidente": ["Requerido"] if not incidente else [],
                    "parcial": ["Requerido"] if parcial is None else []
                }
            }, 422

        try:
            parcial = int(parcial)
            if parcial not in [1, 2, 3]:
                return {"success": False, "message": "El parcial debe ser 1, 2 o 3."}, 422
        except (ValueError, TypeError):
            return {"success": False, "message": "El parcial debe ser un número entero (1, 2 o 3)."}, 422

        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ReportesIndisciplinaService._asegurar_tabla(cursor)

            # Generar Folio: REP-YYYY-XXXX
            year = datetime.now().year
            prefix = f"REP-{year}-"

            cursor.execute("""
                SELECT folio FROM tb_reportes_indisciplina
                WHERE folio LIKE %s
                ORDER BY id DESC
                LIMIT 1
            """, (f"{prefix}%",))
            last_rep = cursor.fetchone()

            if last_rep:
                last_folio = last_rep['folio'] if isinstance(last_rep, dict) else last_rep[0]
                try:
                    last_num = int(last_folio[len(prefix):])
                    next_num = last_num + 1
                except Exception:
                    next_num = 1
            else:
                next_num = 1

            folio = f"{prefix}{str(next_num).zfill(4)}"
            fecha_hoy = date.today().strftime('%Y-%m-%d')

            cursor.execute("""
                INSERT INTO tb_reportes_indisciplina
                (folio, id_alumno, alumno_nombre, tutor_nombre, fecha, incidente, parcial, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (folio, int(id_alumno), str(alumno_nombre).strip(), str(tutor_nombre).strip(), fecha_hoy, str(incidente).strip(), parcial))
            
            conexion.commit()
            new_id = cursor.lastrowid

            cursor.execute("""
                SELECT id, folio, id_alumno, alumno_nombre, tutor_nombre, fecha, incidente, parcial, created_at, updated_at
                FROM tb_reportes_indisciplina
                WHERE id = %s
            """, (new_id,))
            nuevo_reporte = cursor.fetchone()
            nuevo_reporte = ReportesIndisciplinaService._serializar_fechas(nuevo_reporte)

            return {
                "success": True,
                "message": "Reporte de indisciplina registrado correctamente.",
                "data": nuevo_reporte
            }, 201
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    @staticmethod
    def eliminar_reporte(id_reporte):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ReportesIndisciplinaService._asegurar_tabla(cursor)

            cursor.execute("SELECT id FROM tb_reportes_indisciplina WHERE id = %s", (id_reporte,))
            existe = cursor.fetchone()
            if not existe:
                return {"success": False, "message": "Reporte no encontrado."}, 404

            cursor.execute("DELETE FROM tb_reportes_indisciplina WHERE id = %s", (id_reporte,))
            conexion.commit()

            return {"success": True, "message": "Reporte eliminado correctamente."}, 200
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    @staticmethod
    def obtener_conteo_alumno(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ReportesIndisciplinaService._asegurar_tabla(cursor)

            cursor.execute("""
                SELECT parcial, COUNT(*) as total
                FROM tb_reportes_indisciplina
                WHERE id_alumno = %s
                GROUP BY parcial
            """, (int(id_alumno),))
            rows = cursor.fetchall() or []

            counts = {1: 0, 2: 0, 3: 0}
            for r in rows:
                p = r['parcial'] if isinstance(r, dict) else r[0]
                tot = r['total'] if isinstance(r, dict) else r[1]
                if p in counts:
                    counts[p] = int(tot)

            return {
                "success": True,
                "counts": counts
            }
        finally:
            conexion.close()
