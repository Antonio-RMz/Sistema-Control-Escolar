from app.config.conexion import get_connection


class GeneracionesService:
    @staticmethod
    def get_all():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                SELECT id, nombreGeneracion, mesInicio, mesFin, 
                       anioInicio, aniofin, generacion , modalidad
                FROM tb_generaciones
            """
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_generaciones (
                    nombreGeneracion, mesInicio, mesFin, 
                    anioInicio, anioFin,generacion,modalidad, 
                    createBy, updateBy
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get("nombreGeneracion"),
                data.get("mesInicio"),
                data.get("mesFin"),
                data.get("anioInicio"),
                data.get("anioFin"),
                data.get("generacion"),
                data.get("modalidad"),
                data.get("createBy"),
                data.get("updateBy"),
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Generación creada correctamente"}
        finally:
            cursor.close()
            conexion.close()
