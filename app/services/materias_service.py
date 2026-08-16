from app.config.conexion import get_connection
import pymysql


class MateriasService:
    @staticmethod
    def get_materias(page=1, limit=1000, search="", id_materia=None):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            if page < 1:
                page = 1
            if limit < 1:
                limit = 1000
            if limit > 1000:
                limit = 1000

            offset = (page - 1) * limit
            
            conditions = []
            params = []
            
            if id_materia:
                conditions.append("m.id = %s")
                params.append(id_materia)
            
            if search:
                conditions.append("(m.nombreMateria LIKE %s OR m.descripcionMateria LIKE %s OR m.clave LIKE %s)")
                like = f"%{search}%"
                params.extend([like, like, like])
                
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
                
            # Primero obtener el total
            sql_total = f"SELECT COUNT(DISTINCT m.id) AS total FROM tb_materias m {where}"
            cursor.execute(sql_total, params)
            total = cursor.fetchone()["total"]

            # Luego obtener los datos
            sql = f"""
              SELECT 
                    m.id,
                    m.nombreMateria,
                    m.descripcionMateria,
                    m.estatusMateria,
                    m.clave,
                    m.idCentroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    m.id_nivel_academico,
                    na.nombre AS nombreNivelAcademico,
                    IFNULL(
                        GROUP_CONCAT(
                            CONCAT(d.idDocente, ':', d.nombreDocente)
                        ), 
                        ''
                    ) AS docentes
                FROM tb_materias m
                LEFT JOIN tb_centrotrabajo ct ON m.idCentroTrabajo = ct.id
                LEFT JOIN tb_niveles_academicos na ON m.id_nivel_academico = na.id
                LEFT JOIN tb_materiadocente md ON m.id = md.idMateria
                LEFT JOIN tb_docentes d ON md.idDocente = d.idDocente
                {where}
                GROUP BY m.id
                ORDER BY m.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [limit, offset])

            rows = cursor.fetchall()

            for row in rows:
                docentes_str = row["docentes"]
                docentes = []

                if docentes_str:
                    for d in docentes_str.split(","):
                        if ":" in d:
                            id_docente, nombre = d.split(":", 1)
                            docentes.append(
                                {"idDocente": int(id_docente), "nombreDocente": nombre}
                            )

                row["docentes"] = docentes
                
            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
                "search": search,
                "data": rows,
            }

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_materia(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Sanitizar estatusMateria para que coincida con el ENUM ('ACTIVA', 'INACTIVA')
            estatus = str(data.get("estatusMateria", "")).strip().upper()
            if estatus in ["ACTIVO", "ACTIVA"]:
                estatus = "ACTIVA"
            elif estatus in ["INACTIVO", "INACTIVA"]:
                estatus = "INACTIVA"
            else:
                estatus = "ACTIVA"

            id_cct = data.get("idCentroTrabajo") if data.get("idCentroTrabajo") not in ["", None, "null"] else None
            id_nivel = data.get("id_nivel_academico") if data.get("id_nivel_academico") not in ["", None, "null"] else None

            # 🧱 Insertar materia
            query = """
            INSERT INTO tb_materias 
            (nombreMateria, descripcionMateria, estatusMateria, clave, idCentroTrabajo, id_nivel_academico)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    data.get("nombreMateria"),
                    data.get("descripcionMateria"),
                    estatus,
                    data.get("clave"),
                    id_cct,
                    id_nivel,
                ),
            )

            # 🆔 Obtener ID
            id_materia = cursor.lastrowid

            # 📦 Obtener docentes
            docentes = data.get("docentes", [])

            # 🔗 Insertar en tabla puente
            if docentes:
                query_rel = """
                INSERT INTO tb_materiadocente (idMateria, idDocente)
                VALUES (%s, %s)
                """

                for doc in docentes:
                    if isinstance(doc, dict):
                        id_docente = doc.get("idDocente")
                    else:
                        id_docente = doc  # compatibilidad con formato viejo

                    cursor.execute(query_rel, (id_materia, id_docente))

            conexion.commit()

            return {"mensaje": "Materia creada correctamente", "idMateria": id_materia}

        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete_materia(id_materia):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Eliminar relaciones en tablas secundarias para evitar errores de llave foránea
            cursor.execute("DELETE FROM tb_materiadocente WHERE idMateria = %s", (id_materia,))
            cursor.execute("DELETE FROM plan_estudio_materia WHERE idMateria = %s", (id_materia,))
            cursor.execute("DELETE FROM tb_horarios WHERE id_materia = %s", (id_materia,))
            
            # Eliminar la materia
            cursor.execute("DELETE FROM tb_materias WHERE id = %s", (id_materia,))
            conexion.commit()
            return {"mensaje": "Materia eliminada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update_materia(id_materia, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Sanitizar estatusMateria para que coincida con el ENUM ('ACTIVA', 'INACTIVA')
            estatus = str(data.get("estatusMateria", "")).strip().upper()
            if estatus in ["ACTIVO", "ACTIVA"]:
                estatus = "ACTIVA"
            elif estatus in ["INACTIVO", "INACTIVA"]:
                estatus = "INACTIVA"
            else:
                estatus = "ACTIVA"

            id_cct = data.get("idCentroTrabajo") if data.get("idCentroTrabajo") not in ["", None, "null"] else None
            id_nivel = data.get("id_nivel_academico") if data.get("id_nivel_academico") not in ["", None, "null"] else None

            # 🧱 Actualizar datos básicos de la materia
            cursor.execute(
                """
                UPDATE tb_materias 
                SET nombreMateria = %s, descripcionMateria = %s, estatusMateria = %s, clave = %s, idCentroTrabajo = %s, id_nivel_academico = %s
                WHERE id = %s
                """,
                (
                    data.get("nombreMateria"),
                    data.get("descripcionMateria"),
                    estatus,
                    data.get("clave"),
                    id_cct,
                    id_nivel,
                    id_materia,
                ),
            )

            #  Actualizar docentes relacionados (Sincronización)
            # Primero eliminamos todas las asignaciones existentes de la materia
            cursor.execute("DELETE FROM tb_materiadocente WHERE idMateria = %s", (id_materia,))
            
            # Insertamos las nuevas asignaciones si existen
            docentes = data.get("docentes", [])
            if docentes:
                query_rel = """
                INSERT INTO tb_materiadocente (idMateria, idDocente)
                VALUES (%s, %s)
                """
                for doc in docentes:
                    if isinstance(doc, dict):
                        id_docente = doc.get("idDocente")
                    else:
                        id_docente = doc  # compatibilidad con formato simple
                    
                    if id_docente:
                        cursor.execute(query_rel, (id_materia, id_docente))

            conexion.commit()
            return {"mensaje": "Materia actualizada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
