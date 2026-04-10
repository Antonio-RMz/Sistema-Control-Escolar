from app.config.conexion import get_connection

class AlumnosService:
    @staticmethod
    def get_alumnos(page=1, limit=50, idGeneracion=None, idGrupo=None, search=''):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            if page < 1: page = 1
            if limit < 1: limit = 50
            if limit > 200: limit = 200
            
            offset = (page - 1) * limit
            where = []
            valores = []

            if idGeneracion:
                where.append("idGeneracion = %s")
                valores.append(idGeneracion)

            if idGrupo:
                where.append("idGrupo = %s")
                valores.append(idGrupo)

            if search:
                palabras = search.strip().split()
                for palabra in palabras:
                    where.append("(nombre LIKE %s OR apPaterno LIKE %s OR apMaterno LIKE %s)")
                    like = f"%{palabra}%"
                    valores.extend([like, like, like])

            where_sql = "WHERE " + " AND ".join(where) if where else ""

            # Total de registros
            sql_total = f"SELECT COUNT(*) AS total FROM tb_alumnos {where_sql}"
            cursor.execute(sql_total, valores)
            total = cursor.fetchone()["total"]

            # Consulta paginada
            sql_datos = f"""
                SELECT 
                    idAlumno, nombre, apPaterno, apMaterno, fechaNacimiento,
                    tutor, parentesco, calle, colonia, localidad, municipio,
                    telefonoTutor, celularAlumno, correoAlumno,
                    escuelaProcedencia, observaciones, idGeneracion, idGrupo
                FROM tb_alumnos
                {where_sql}
                ORDER BY idAlumno ASC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, valores + [limit, offset])
            alumnos = cursor.fetchall()

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "search": search,
                "data": alumnos
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_alumno(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_alumnos (
                    nombre, apPaterno, apMaterno, fechaNacimiento, tutor, 
                    parentesco, calle, colonia, localidad, municipio, 
                    telefonoTutor, celularAlumno, correoAlumno, 
                    escuelaProcedencia, observaciones, idGeneracion, idGrupo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get('nombre'), data.get('apPaterno'), data.get('apMaterno'),
                data.get('fechaNacimiento'), data.get('tutor'), data.get('parentesco'),
                data.get('calle'), data.get('colonia'), data.get('localidad'),
                data.get('municipio'), data.get('telefonoTutor'), data.get('celularAlumno'),
                data.get('correoAlumno'), data.get('escuelaProcedencia'),
                data.get('observaciones'), data.get('idGeneracion'), data.get('idGrupo')
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Alumno creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
