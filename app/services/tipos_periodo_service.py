from app.config.conexion import get_connection


class TiposPeriodoService:
    @staticmethod
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
