from app.config.conexion import get_connection


class CentrosTrabajoService:
    @staticmethod
    def get_centros_trabajo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT 
                    c.id, 
                    c.clave, 
                    c.nombre, 
                    c.direccion, 
                    c.telefono, 
                    c.correo,
                    c.idPrograma, 
                    p.nombrePrograma,
                    c.idTipoPeriodo, 
                    tp.nombrePeriodo
                FROM tb_centrotrabajo c
                LEFT JOIN tb_programas p ON p.id = c.idPrograma
                LEFT JOIN tb_tipoperiodo tp ON tp.id = c.idTipoPeriodo
                ORDER BY c.id ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_by_id(id_cct):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT 
                    c.id, 
                    c.clave, 
                    c.nombre, 
                    c.direccion, 
                    c.telefono, 
                    c.correo,
                    c.idPrograma, 
                    p.nombrePrograma,
                    c.idTipoPeriodo, 
                    tp.nombrePeriodo
                FROM tb_centrotrabajo c
                LEFT JOIN tb_programas p ON p.id = c.idPrograma
                LEFT JOIN tb_tipoperiodo tp ON tp.id = c.idTipoPeriodo
                WHERE c.id = %s
            """
            cursor.execute(query, (id_cct,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_centro_trabajo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_centrotrabajo (clave, nombre, direccion, telefono, correo, idPrograma, idTipoPeriodo) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    data.get("clave"),
                    data.get("nombre"),
                    data.get("direccion"),
                    data.get("telefono"),
                    data.get("correo"),
                    data.get("idPrograma"),
                    data.get("idTipoPeriodo"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Centro de trabajo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
