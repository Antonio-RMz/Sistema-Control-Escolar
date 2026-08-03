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
    def get_materias(page=1, limit=50, search=""):
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
            
            where = ""
            params = []
            
            if search:
                where = "WHERE m.nombreMateria LIKE %s OR m.descripcionMateria LIKE %s OR m.clave LIKE %s"
                like = f"%{search}%"
                params.extend([like, like, like])
                
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
                    data.get("estatusMateria"),
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
    # Métodos get para docentes
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
                    fechaNacimiento
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
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente,nivelEstudios, fechaNacimiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente creado correctamente"}
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

    @staticmethod
    def create_horario_grupo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("id_grupo"),
                    data.get("id_materia"),
                    data.get("id_docente"),
                    data.get("diaSemana"),
                    data.get("horaInicio"),
                    data.get("horaFin"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Horario de grupo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
    @staticmethod
    def getHorariosGrupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            sql = """
                SELECT
                    id_horario AS id,
                    id_grupo,
                    id_materia,
                    id_docente,
                    diaSemana,
                    TIME_FORMAT(horaInicio, '%%H:%%i:%%s') AS horaInicio,
                    TIME_FORMAT(horaFin, '%%H:%%i:%%s') AS horaFin
                FROM tb_horarios
                WHERE id_grupo = %s
                ORDER BY diaSemana, horaInicio
            """
            cursor.execute(sql, (id_grupo,))
            horarios = cursor.fetchall()
            return horarios
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
