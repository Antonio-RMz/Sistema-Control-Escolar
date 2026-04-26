from app.config.conexion import get_connection

class GruposService:
    @staticmethod
    #para obtener todos los grupos con búsqueda y paginación
    def get_all(page=1, limit=50, search=''):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validaciones de entrada para consistencia
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
                where = " WHERE clave LIKE %s "
                params.append(f"%{search}%")
            
            # Obtener el total para la paginación
            sql_total = f"SELECT COUNT(*) AS total FROM tb_grupos {where}"
            cursor.execute(sql_total, params)
            total = cursor.fetchone()["total"]

            # Obtener los datos paginados
            sql_datos = f"""
                SELECT id, clave, fechaCreacion, fechaInicio, fechaFin,
                id_centroTrabajo, id_tipoPeriodo, id_planEstudios
                FROM tb_grupos
                {where}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, params + [limit, offset])
            data = cursor.fetchall()

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "search": search,
                "data": data
            }
        finally:
            cursor.close()
            conexion.close()
#para crear los grupos
    @staticmethod
    def create(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_grupos (
                    clave, fechaCreacion, fechaInicio, fechaFin, 
                    id_centroTrabajo, id_tipoPeriodo, id_planEstudios
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get('clave'), data.get('fechaCreacion'), data.get('fechaInicio'),
                data.get('fechaFin'), data.get('id_centroTrabajo'),
                data.get('id_tipoPeriodo'), data.get('id_planEstudios')
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Grupo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_alumnos_by_grupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT a.*
                FROM tb_alumnos a
                INNER JOIN tb_alumnogrupo ag 
                    ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s
            """
            cursor.execute(query, (id_grupo,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
