from annotated_types import doc

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
    def get_materias():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                """
              SELECT 
                    m.id,
                    m.nombreMateria,
                    m.descripcionMateria,
                    m.estatusMateria,
                    IFNULL(
                        GROUP_CONCAT(
                            CONCAT(d.idDocente, ':', d.nombreDocente)
                        ), 
                        ''
                    ) AS docentes
                FROM tb_materias m
                LEFT JOIN tb_materiadocente md ON m.id = md.idMateria
                LEFT JOIN tb_docentes d ON md.idDocente = d.idDocente
                GROUP BY m.id;
            """
            )

            rows = cursor.fetchall()

            for row in rows:
                docentes_str = row["docentes"]
                docentes = []

                if docentes_str:
                    for d in docentes_str.split(","):
                        id_docente, nombre = d.split(":")
                        docentes.append(
                            {"idDocente": int(id_docente), "nombreDocente": nombre}
                        )

                row["docentes"] = docentes
            return rows

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
            (nombreMateria, descripcionMateria, estatusMateria)
            VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    data.get("nombreMateria"),
                    data.get("descripcionMateria"),
                    data.get("estatusMateria"),
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

    # Métodos get para planes de estudio
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
            conexion.commit()
            return {"mensaje": "Plan de estudios creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
