from app.config.conexion import get_connection

class GeneracionesService:
    @staticmethod
    def get_all():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, nombreGeneracion, mesInicio, mesFin, 
                       anioInicio, aniofin, numeroGeneracion 
                FROM tb_generaciones
            """)
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
                INSERT INTO tb_generaciones (numeroGeneracion, periodo, createBy, UpdateBy)
                VALUES (%s, %s, %s, %s)
            """
            values = (
                data.get('numeroGeneracion'), data.get('periodo'),
                data.get('createBy'), data.get('UpdateBy')
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Generación creada correctamente"}
        finally:
            cursor.close()
            conexion.close()
