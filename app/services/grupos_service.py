from app.config.conexion import get_connection

class GruposService:
    @staticmethod
    #para obtener todos los grupos
    def get_all():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, clave, fechaCreacion, fechaInicio, fechaFin,
                id_centroTrabajo, id_tipoPeriodo, id_planEstudios
                FROM tb_grupos
            """)
            return cursor.fetchall()
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
