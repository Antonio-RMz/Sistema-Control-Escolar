from app.config.conexion import get_connection
import pymysql


class CatalogosService:
    # Métodos get para centros de trabajo
    @staticmethod
    def get_centros_trabajo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "SELECT id, nombre, direccion, telefono, correo FROM tb_centrotrabajo"
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_alumno_equivalencia(page=1, limit=50, search=""):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            if page < 1:
                page = 1
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200

            offset = (page - 1) * limit
            where = ["UPPER(a.equivalencia) = 'SI'"]
            valores = []

            if search:
                palabras = search.strip().split()
                for palabra in palabras:
                    where.append(
                        "(a.nombre LIKE %s OR a.apPaterno LIKE %s OR a.apMaterno LIKE %s)"
                    )
                    like = f"%{palabra}%"
                    valores.extend([like, like, like])

            where_sql = "WHERE " + " AND ".join(where)

            # Total de registros
            sql_total = f"SELECT COUNT(*) AS total FROM tb_alumnos a {where_sql}"
            cursor.execute(sql_total, valores)
            total = cursor.fetchone()["total"]

            # Consulta paginada
            sql_datos = f"""
                SELECT 
                    a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.fechaNacimiento,
                    a.tutor, a.parentesco, a.calle, a.colonia, a.localidad, a.municipio,
                    a.telefonoTutor, a.celularAlumno, a.correoAlumno,
                    a.escuelaProcedencia, a.observaciones, a.idGeneracion, a.idGrupo, a.equivalencia,
                    g.generacion AS nombreGeneracionTexto
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                {where_sql}
                ORDER BY a.idAlumno ASC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, valores + [limit, offset])
            data = cursor.fetchall()

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
                "search": search,
                "data": data,
            }
        finally:
            cursor.close()
            conexion.close()

    # Método para crear un nuevo centro de trabajo
    @staticmethod
    def create_centro_trabajo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_centrotrabajo (clave, nombre, direccion, telefono, correo) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("clave"),
                    data.get("nombre"),
                    data.get("direccion"),
                    data.get("telefono"),
                    data.get("correo"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Centro de trabajo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    # Métodos get para tipos de periodo
    def get_tipos_periodo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "SELECT id, nombrePeriodo, descripcionPeriodo FROM tb_tipoperiodo"
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    # Método para crear un nuevo tipo de periodo
    @staticmethod
    def get_materias(page=1, limit=50, search="", id_materia=None):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            if page < 1:
                page = 1
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200

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
                    IFNULL(
                        GROUP_CONCAT(
                            CONCAT(d.idDocente, ':', d.nombreDocente)
                        ), 
                        ''
                    ) AS docentes
                FROM tb_materias m
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

    # Método para crear una nueva materia
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

            # 🧱 Insertar materia
            query = """
            INSERT INTO tb_materias 
            (nombreMateria, descripcionMateria, estatusMateria, clave)
            VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    data.get("nombreMateria"),
                    data.get("descripcionMateria"),
                    estatus,
                    data.get("clave"),
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

            # 🧱 Actualizar datos básicos de la materia
            cursor.execute(
                """
                UPDATE tb_materias 
                SET nombreMateria = %s, descripcionMateria = %s, estatusMateria = %s, clave = %s
                WHERE id = %s
                """,
                (
                    data.get("nombreMateria"),
                    data.get("descripcionMateria"),
                    estatus,
                    data.get("clave"),
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
    # Métodos get para docentes
    #### -------------------- MATERIAS -------------------
    @staticmethod
    def get_docentes(page, limit, search, status):
        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            offset = (page - 1) * limit

            sql = """
                SELECT 
                    idDocente, 
                    nombreDocente, 
                    apPaternoDocente, 
                    apMaternoDocente, 
                    correoDocente, 
                    telefonoDocente, 
                    statusDocente, 
                    observacionesDocente,
                    nivelEstudios,
                    fechaNacimiento,
                    idBiometrico
                FROM tb_docentes
                WHERE 1=1
            """

            params = []

            #  Búsqueda
            if search:
                sql += """
                    AND (
                        nombreDocente LIKE %s OR 
                        apPaternoDocente LIKE %s OR 
                        apMaternoDocente LIKE %s
                    )
                """
                like = f"%{search}%"
                params.extend([like, like, like])

            # Filtro por status
            if status:
                sql += " AND statusDocente = %s"
                params.append(status)

            #  Paginación
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(sql, params)
            data = cursor.fetchall()

            return {"data": data, "page": page, "limit": limit}

        finally:
            cursor.close()
            conexion.close()

    # Método para crear un nuevo docente
    @staticmethod
    def create_docente(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente,nivelEstudios, fechaNacimiento, idBiometrico)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def update_docente(id_docente, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE tb_docentes 
                SET nombreDocente = %s, apPaternoDocente = %s, apMaternoDocente = %s, 
                    correoDocente = %s, telefonoDocente = %s, statusDocente = %s, 
                    observacionesDocente = %s, nivelEstudios = %s, fechaNacimiento = %s,
                    idBiometrico = %s
                WHERE idDocente = %s
            """
            cursor.execute(
                query,
                (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                    id_docente,
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente actualizado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def delete_docente(idDocente):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Desvincular materias asociadas al docente (poner a NULL) para no eliminarlas
            cursor.execute("UPDATE tb_materias SET idDocente = NULL WHERE idDocente = %s", (idDocente,))
            
            # 2. Eliminar relaciones en tablas secundarias para evitar errores de llave foránea
            cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_cursoextracurricular WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_grupodocentes WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_horarios WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_materiadocente WHERE idDocente = %s", (idDocente,))
            
            # 3. Eliminar el docente
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (idDocente,))
            conexion.commit()
            return {"mensaje": "Docente eliminado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    # Métodos crear planes de estudio
    @staticmethod
    def create_plan_estudios(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_planesestudio (nombrePlan, descripcionPlan, estatusPlan) VALUES (%s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("nombrePlan"),
                    data.get("descripcionPlan"),
                    data.get("estatusPlan"),
                ),
            )
            
            # Obtener el id insertado
            id_plan = cursor.lastrowid
            
            # Recuperar materias enviadas
            materias = data.get("idmaterias", [])
            
            if materias:
                query_rel = "INSERT INTO plan_estudio_materia (idPlanEstudio, idMateria) VALUES (%s, %s)"
                for mat in materias:
                    if isinstance(mat, dict):
                        id_materia = mat.get("idMateria") or mat.get("id")
                    else:
                        id_materia = mat
                        
                    if id_materia:
                        cursor.execute(query_rel, (id_plan, id_materia))

            conexion.commit()
            return {"mensaje": "Plan de estudios creado correctamente", "idPlanEstudio": id_plan}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_planes_estudio():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("""
                SELECT 
                    p.id,
                    p.nombrePlan, 
                    p.descripcionPlan, 
                    p.estatusPlan,
                    IFNULL(GROUP_CONCAT(DISTINCT pm.idMateria), '') AS idmaterias
                FROM tb_planesestudio p
                LEFT JOIN plan_estudio_materia pm ON p.id = pm.idPlanEstudio
                GROUP BY p.id
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                materias_str = row["idmaterias"]
                materias = []
                if materias_str:
                    for m in materias_str.split(","):
                        materias.append(int(m))
                row["idmaterias"] = materias
                
            return rows
        finally:
            cursor.close()
            conexion.close()

    # metodo para asignar alumno a grupo
    @staticmethod
    def create_alumno_grupo(data):

        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_alumnoGrupo (idAlumno, idGrupo) VALUES (%s, %s)"
            cursor.execute(
                query,
                (
                    data.get("idAlumno"),
                    data.get("idGrupo"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Alumno asignado al grupo correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_tipo_periodo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_tipoperiodo (nombrePeriodo, descripcionPeriodo) VALUES (%s, %s)"
            cursor.execute(
                query,
                (
                    data.get("nombrePeriodo"),
                    data.get("descripcionPeriodo"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Tipo de periodo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_curso_extracurricular(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_cursoExtracurricular (nombre,descripcion,fechaInicio,fechaFin,idCentroTrabajo,idDocente) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("nombre"),
                    data.get("descripcion"),
                    data.get("fechaInicio"),
                    data.get("fechaFin"),
                    data.get("idCentroTrabajo"),
                    data.get("idDocente"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Curso extracurricular creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_cursos_extracurriculares():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("""
                SELECT 
                    ce.id,
                    ce.nombre,
                    ce.descripcion,
                    ce.fechaInicio,
                    ce.fechaFin,
                    ct.nombre AS nombreCentroTrabajo,
                    CONCAT(d.nombreDocente, ' ', d.apPaternoDocente, ' ', d.apMaternoDocente) AS nombreDocente
                FROM tb_cursoExtracurricular ce
                LEFT JOIN tb_centrotrabajo ct ON ce.idCentroTrabajo = ct.id
                LEFT JOIN tb_docentes d ON ce.idDocente = d.idDocente
                """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
###-----HORARIOS----------
    @staticmethod
    def create_horario_grupo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            id_grupo = data.get("id_grupo")
            diaSemana = data.get("diaSemana")
            horaInicio = data.get("horaInicio") or data.get("horainicio")
            horaFin = data.get("horaFin") or data.get("horafin")
            id_docente = data.get("id_docente")
            aula = data.get("aula")
            # Soporta tanto un arreglo de IDs en 'materias' como una sola materia 'id_materia'
            materias = data.get("materias", [])
            if not materias:
                if data.get("id_materia"):
                    materias = [data.get("id_materia")]

            if not materias or not id_docente:
                return {"error": "Faltan datos de la materia o docente"}, 400

            query = "INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula) VALUES (%s, %s, %s, %s, %s, %s,%s)"
            
            # Insertar todas las materias para el mismo docente de forma atómica
            for id_materia in materias:
                cursor.execute(
                    query,
                    (
                        id_grupo,
                        id_materia,
                        id_docente,
                        diaSemana,
                        horaInicio,
                        horaFin,
                        aula
                    )
                )
            conexion.commit()
            return {"mensaje": "Horario de grupo creado correctamente"}
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def getHorariosGrupo(id_grupo, agrupado=False):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
                SELECT
                    h.id_horario AS id,
                    h.id_grupo,
                    h.id_materia,
                    h.id_docente,
                    h.diaSemana,
                    h.aula,
                    TIME_FORMAT(h.horaInicio, '%%H:%%i:%%s') AS horaInicio,
                    TIME_FORMAT(h.horaFin, '%%H:%%i:%%s') AS horaFin,
                    m.nombreMateria AS materia_nombre,
                    CONCAT(d.nombreDocente, ' ', d.apPaternoDocente, ' ', d.apMaternoDocente) AS docente_nombre
                FROM tb_horarios h
                LEFT JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s
                ORDER BY h.diaSemana, h.horaInicio
            """
            cursor.execute(sql, (id_grupo,))
            horarios = cursor.fetchall()

            if not agrupado:
                return horarios

            # Agrupar por día, rango de hora, docente y aula
            grouped = {}
            for h in horarios:
                key = (h["diaSemana"], h["horaInicio"], h["horaFin"], h["id_docente"], h["aula"])
                if key not in grouped:
                    grouped[key] = {
                        "diaSemana": h["diaSemana"],
                        "horaInicio": h["horaInicio"],
                        "horaFin": h["horaFin"],
                        "id_docente": h["id_docente"],
                        "docente_nombre": h["docente_nombre"],
                        "aula": h["aula"],
                        "clases": []
                    }
                grouped[key]["clases"].append({
                    "id_horario": h["id"],
                    "id_materia": h["id_materia"],
                    "materia_nombre": h["materia_nombre"],
                    "id_docente": h["id_docente"],
                    "docente_nombre": h["docente_nombre"]
                })

            return list(grouped.values())
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def validacionHorario(id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin):
        import pymysql
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            day_map = {
                "lunes": 1, "martes": 2, "miercoles": 3, "miércoles": 3,
                "jueves": 4, "viernes": 5, "sabado": 6, "sábado": 6,
                "domingo": 7
            }
            if isinstance(diaSemana, str):
                dia_semana_val = day_map.get(diaSemana.lower(), diaSemana)
            else:
                dia_semana_val = diaSemana

            # Buscamos si el docente tiene otra clase en ese mismo día y hora en un GRUPO DIFERENTE
            cursor.execute("""
                SELECT 
                    h.id_grupo,
                    g.clave AS grupo_clave,
                    m.nombreMateria AS materia_nombre
                FROM tb_horarios h
                LEFT JOIN tb_grupos g ON h.id_grupo = g.id
                LEFT JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s
                AND h.diaSemana = %s
                AND h.horaInicio = %s
                AND h.id_grupo != %s
            """, (id_docente, dia_semana_val, horaInicio, id_grupo))
            existe_empalme = cursor.fetchone()
            
            if existe_empalme:
                return {
                    "success": False,
                    "mensaje": f"El docente ya tiene una clase asignada en el grupo '{existe_empalme['grupo_clave']}' con la materia '{existe_empalme['materia_nombre']}' en este horario."
                }
            return {
                "success": True,
                "mensaje": "El docente está disponible para ese horario."
            }
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def deleteHorarioGrupo(id_horario):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM tb_horarios WHERE id_horario = %s", (id_horario,))
            conexion.commit()
            return {"mensaje": "Horario de grupo eliminado correctamente"}
        finally:
            cursor.close()
            conexion.close()
#metodo para obtener el niveles academicos 
    @staticmethod
    def get_nivel_academico():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT * FROM tb_niveles_academicos")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_horas_docentes(fecha_inicio_str, fecha_fin_str):
        import datetime
        from datetime import timedelta
        
        try:
            d_inicio = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            d_fin = datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Las fechas deben tener el formato YYYY-MM-DD")

        if d_inicio > d_fin:
            raise ValueError("La fecha de inicio debe ser menor o igual a la fecha de fin")

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # 1. Obtener todos los docentes activos
            cursor.execute("""
                SELECT 
                    idDocente, 
                    CONCAT(nombreDocente, ' ', COALESCE(apPaternoDocente, ''), ' ', COALESCE(apMaternoDocente, '')) AS docente
                FROM tb_docentes
                WHERE statusDocente = 'ACTIVO'
                ORDER BY nombreDocente, apPaternoDocente, apMaternoDocente
            """)
            docentes = cursor.fetchall()

            if not docentes:
                return []

            # 2. Obtener los horarios de grupos vigentes dentro del rango solicitado
            cursor.execute("""
                SELECT 
                    h.id_docente,
                    h.diaSemana,
                    h.horaInicio,
                    h.horaFin,
                    g.fechaInicio,
                    g.fechaFin
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                WHERE g.fechaInicio <= %s AND g.fechaFin >= %s
            """, (fecha_fin_str, fecha_inicio_str))
            horarios = cursor.fetchall()

            # Organizar horarios por docente
            horarios_por_docente = {}
            for h in horarios:
                id_doc = h['id_docente']
                if id_doc not in horarios_por_docente:
                    horarios_por_docente[id_doc] = []
                horarios_por_docente[id_doc].append(h)

            # Generar la lista de fechas en el rango
            dias_rango = []
            curr = d_inicio
            while curr <= d_fin:
                dias_rango.append(curr)
                curr += timedelta(days=1)

            resultado = []

            for doc in docentes:
                id_docente = doc['idDocente']
                docente_nombre = doc['docente'].strip()
                slots_docente = horarios_por_docente.get(id_docente, [])

                dias_reporte = []
                for d in dias_rango:
                    db_weekday = d.weekday() + 1
                    fecha_str = d.strftime("%Y-%m-%d")

                    # Filtrar horarios del docente activos en este día de la semana y vigentes en esta fecha
                    # Agrupamos por (horaInicio, horaFin) para evitar contar múltiples materias en la misma hora
                    slots_dia_map = {}
                    for h in slots_docente:
                        # Convertir fechas de mysql a date de python si vienen como datetime.date
                        h_fecha_inicio = h['fechaInicio']
                        h_fecha_fin = h['fechaFin']
                        if isinstance(h_fecha_inicio, datetime.datetime):
                            h_fecha_inicio = h_fecha_inicio.date()
                        if isinstance(h_fecha_fin, datetime.datetime):
                            h_fecha_fin = h_fecha_fin.date()

                        if h['diaSemana'] == db_weekday and h_fecha_inicio <= d <= h_fecha_fin:
                            key = (h['horaInicio'], h['horaFin'])
                            slots_dia_map[key] = h

                    if not slots_dia_map:
                        dias_reporte.append({
                            "fecha": fecha_str,
                            "total": 0,
                            "real": 0
                        })
                        continue

                    # Calcular total de horas
                    total_minutos = 0
                    intervals = []
                    for start_td, end_td in slots_dia_map.keys():
                        
                        if isinstance(start_td, str):
                            h, m, s_val = map(int, start_td.split(':'))
                            start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(start_td, datetime.time):
                            start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                            
                        if isinstance(end_td, str):
                            h, m, s_val = map(int, end_td.split(':'))
                            end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(end_td, datetime.time):
                            end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)

                        diff_min = (end_td - start_td).total_seconds() / 60.0
                        total_minutos += diff_min
                        intervals.append((start_td.total_seconds() / 60.0, end_td.total_seconds() / 60.0))

                    total_horas = total_minutos / 60.0

                    # Calcular real de horas (unión de intervalos)
                    intervals.sort(key=lambda x: x[0])
                    merged = []
                    for start, end in intervals:
                        if not merged:
                            merged.append([start, end])
                        else:
                            prev_start, prev_end = merged[-1]
                            if start <= prev_end:
                                merged[-1][1] = max(prev_end, end)
                            else:
                                merged.append([start, end])
                    
                    real_minutos = sum(end - start for start, end in merged)
                    real_horas = real_minutos / 60.0

                    def format_hours(h):
                        h_round = round(h, 2)
                        return int(h_round) if h_round.is_integer() else h_round

                    dias_reporte.append({
                        "fecha": fecha_str,
                        "total": format_hours(total_horas),
                        "real": format_hours(real_horas)
                    })

                resultado.append({
                    "id_docente": id_docente,
                    "docente": docente_nombre,
                    "dias": dias_reporte
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_detalle_horas_docente(id_docente, fecha_str):
        import datetime
        from datetime import timedelta
        
        try:
            d_fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD")

        # diaSemana: 1 (Lunes) a 7 (Domingo)
        db_weekday = d_fecha.weekday() + 1

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # Consultar los horarios vigentes para el docente en este día de la semana y fecha
            # Un grupo está vigente si g.fechaInicio <= d_fecha <= g.fechaFin
            cursor.execute("""
                SELECT 
                    m.nombreMateria AS materia,
                    g.clave AS grupo,
                    h.aula,
                    h.horaInicio,
                    h.horaFin
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s 
                  AND h.diaSemana = %s
                  AND g.fechaInicio <= %s 
                  AND g.fechaFin >= %s
                ORDER BY h.horaInicio, m.nombreMateria
            """, (id_docente, db_weekday, fecha_str, fecha_str))
            
            rows = cursor.fetchall()
            
            resultado = []
            for r in rows:
                start_td = r['horaInicio']
                end_td = r['horaFin']
                
                # Convertir time/timedelta/string a timedelta para calcular duracion
                if isinstance(start_td, str):
                    h, m, s_val = map(int, start_td.split(':'))
                    start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    start_str = r['horaInicio']
                elif isinstance(start_td, datetime.time):
                    start_str = start_td.strftime("%H:%M:%S")
                    start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                else: # timedelta
                    tot_sec = int(start_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    start_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                if isinstance(end_td, str):
                    h, m, s_val = map(int, end_td.split(':'))
                    end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    end_str = r['horaFin']
                elif isinstance(end_td, datetime.time):
                    end_str = end_td.strftime("%H:%M:%S")
                    end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)
                else: # timedelta
                    tot_sec = int(end_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    end_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                diff_hours = (end_td - start_td).total_seconds() / 3600.0
                
                def format_hours(h):
                    h_round = round(h, 2)
                    return int(h_round) if h_round.is_integer() else h_round

                resultado.append({
                    "materia": r['materia'],
                    "grupo": r['grupo'],
                    "aula": r['aula'],
                    "hora_inicio": start_str,
                    "hora_fin": end_str,
                    "duracion": format_hours(diff_hours)
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()