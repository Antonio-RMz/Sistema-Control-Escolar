from app.config.conexion import get_connection
import datetime

class GruposService:
    @staticmethod
    # para obtener todos los grupos con búsqueda y paginación
    def get_all(page=1, limit=50, search=""):
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
                where = " WHERE g.clave LIKE %s "
                params.append(f"%{search}%")

            # Obtener el total para la paginación
            sql_total = f"SELECT COUNT(DISTINCT g.id) AS total FROM tb_grupos g {where}"
            cursor.execute(sql_total, params)
            total = cursor.fetchone()["total"]

            # Obtener los datos paginados
            sql_datos = f"""
                SELECT g.id, g.clave, g.fechaCreacion, g.fechaInicio, g.fechaFin,
                g.id_centroTrabajo, g.id_tipoPeriodo, g.id_planEstudios,
                IFNULL(GROUP_CONCAT(gd.dia), '') AS diasClase
                FROM tb_grupos g
                LEFT JOIN tb_grupodias gd ON g.id = gd.idGrupo
                {where}
                GROUP BY g.id
                ORDER BY g.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, params + [limit, offset])
            data = cursor.fetchall()
            
            for row in data:
                dias_str = row["diasClase"]
                row["diasClase"] = dias_str.split(",") if dias_str else []

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "search": search,
                "data": data,
            }
        finally:
            cursor.close()
            conexion.close()

    # para crear los grupos
    @staticmethod
    def create(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            fecha_inicio_str = data.get("fechaInicio")
            fecha_fin = data.get("fechaFin")
            duracion_semanas = data.get("duracionSemanas")
            
            if duracion_semanas and fecha_inicio_str:
                # Calcular fechaFin sumando semanas
                fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
                fecha_fin_dt = fecha_inicio_dt + datetime.timedelta(weeks=int(duracion_semanas))
                fecha_fin = fecha_fin_dt.strftime("%Y-%m-%d")

            query = """
                INSERT INTO tb_grupos (
                    clave, fechaCreacion, fechaInicio, fechaFin, 
                    id_centroTrabajo, id_tipoPeriodo, id_planEstudios,modalidadHorario
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get("clave"),
                data.get("fechaCreacion"),
                fecha_inicio_str,
                fecha_fin,
                data.get("id_centroTrabajo"),
                data.get("id_tipoPeriodo"),
                data.get("id_planEstudios"),
                data.get("modalidadHorario")
            )
            cursor.execute(query, values)
            
            id_grupo = cursor.lastrowid
            
            # Guardar los días de clase si vienen en el payload
            dias_clase = data.get("diasClase", [])
            if dias_clase:
                query_dias = "INSERT INTO tb_grupodias (idGrupo, dia) VALUES (%s, %s)"
                for dia in dias_clase:
                    cursor.execute(query_dias, (id_grupo, dia))
                    
            conexion.commit()
            return {"mensaje": "Grupo creado correctamente", "idGrupo": id_grupo}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
#para obtener los alumnos por grupo
    @staticmethod
    def get_alumnos_by_grupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT a.*
                FROM tb_alumnos a
                INNER JOIN tb_alumnoGrupo ag 
                    ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s
            """
            cursor.execute(query, (id_grupo,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
   #para obtener los datos de un grupo
    @staticmethod
    def update(id_grupo, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            fecha_inicio_str = data.get("fechaInicio")
            fecha_fin = data.get("fechaFin")

            query = """
                UPDATE tb_grupos 
                SET
                    clave = %s,
                    fechaCreacion = %s,
                    fechaInicio = %s,
                    fechaFin = %s,
                    id_centroTrabajo = %s,
                    id_tipoPeriodo = %s,
                    id_planEstudios = %s,
                    modalidadHorario = %s
                WHERE id = %s
            """
            values = (
                data.get("clave"),
                data.get("fechaCreacion"),
                fecha_inicio_str,
                fecha_fin,
                data.get("id_centroTrabajo"),
                data.get("id_tipoPeriodo"),
                data.get("id_planEstudios"),
                data.get("modalidadHorario"),
                id_grupo
            )
            cursor.execute(query, values)
                    
            conexion.commit()
            return {"mensaje": "Grupo actualizado correctamente", "idGrupo": id_grupo}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    #para obtener la informacion de un solo grupo
    def get_grupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT * FROM tb_grupos WHERE id = %s
            """
            cursor.execute(query, (id_grupo,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()
    