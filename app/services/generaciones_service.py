from app.config.conexion import get_connection


class GeneracionesService:
    @staticmethod
    def get_all(id_centro_trabajo=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            where = []
            params = []
            if id_centro_trabajo:
                where.append("g.id_centroTrabajo = %s")
                params.append(id_centro_trabajo)

            where_sql = "WHERE " + " AND ".join(where) if where else ""
            query = f"""
                SELECT 
                    g.id, 
                    g.id_centroTrabajo, 
                    c.nombre AS nombreCentroTrabajo,
                    g.nombreGeneracion, 
                    g.mesInicio, 
                    g.mesFin, 
                    g.anioInicio, 
                    g.aniofin, 
                    g.generacion
                FROM tb_generaciones g
                LEFT JOIN tb_centrotrabajo c ON c.id = g.id_centroTrabajo
                {where_sql}
                ORDER BY g.id DESC
            """
            cursor.execute(query, params)
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
                    id_centroTrabajo, nombreGeneracion, mesInicio, mesFin, 
                    anioInicio, aniofin, generacion, 
                    createBy, updateBy
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get("id_centroTrabajo") or data.get("idCentroTrabajo"),
                data.get("nombreGeneracion"),
                data.get("mesInicio"),
                data.get("mesFin"),
                data.get("anioInicio"),
                data.get("aniofin") or data.get("anioFin"),
                data.get("generacion"),
                data.get("createBy"),
                data.get("updateBy"),
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Generación creada correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update(id_generacion, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE tb_generaciones
                SET
                    id_centroTrabajo = %s,
                    nombreGeneracion = %s,
                    mesInicio = %s,
                    mesFin = %s,
                    anioInicio = %s,
                    aniofin = %s,
                    generacion = %s,
                    updateBy = %s
                WHERE id = %s
            """
            values = (
                data.get("id_centroTrabajo") or data.get("idCentroTrabajo"),
                data.get("nombreGeneracion"),
                data.get("mesInicio"),
                data.get("mesFin"),
                data.get("anioInicio"),
                data.get("aniofin") or data.get("anioFin"),
                data.get("generacion"),
                data.get("updateBy"),
                id_generacion
            )
            cursor.execute(query, values)
            conexion.commit()
            return {"mensaje": "Generación actualizada correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete(id_generacion):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM tb_generaciones WHERE id = %s", (id_generacion,))
            conexion.commit()
            return {"mensaje": "Generación eliminada correctamente"}
        finally:
            cursor.close()
            conexion.close()
