from app.config.conexion import get_connection


class CentrosTrabajoService:
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
