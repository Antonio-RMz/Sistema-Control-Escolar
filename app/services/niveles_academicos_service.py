from app.config.conexion import get_connection
import pymysql


class NivelesAcademicosService:
    @staticmethod
    def get_nivel_academico(id_centro_trabajo=None, id_tipo_periodo=None):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            if id_centro_trabajo:
                query = """
                    SELECT 
                        n.id, 
                        n.nombre, 
                        n.tipo, 
                        n.numero, 
                        n.duracion_semanas, 
                        n.activo,
                        n.id_tipoPeriodo, 
                        tp.nombrePeriodo
                    FROM tb_niveles_academicos n
                    INNER JOIN tb_centrotrabajo c ON c.idTipoPeriodo = n.id_tipoPeriodo
                    LEFT JOIN tb_tipoperiodo tp ON tp.id = n.id_tipoPeriodo
                    WHERE c.id = %s AND n.activo = 1
                    ORDER BY n.numero ASC
                """
                cursor.execute(query, (id_centro_trabajo,))
            elif id_tipo_periodo:
                query = """
                    SELECT 
                        n.id, 
                        n.nombre, 
                        n.tipo, 
                        n.numero, 
                        n.duracion_semanas, 
                        n.activo,
                        n.id_tipoPeriodo, 
                        tp.nombrePeriodo
                    FROM tb_niveles_academicos n
                    LEFT JOIN tb_tipoperiodo tp ON tp.id = n.id_tipoPeriodo
                    WHERE n.id_tipoPeriodo = %s AND n.activo = 1
                    ORDER BY n.numero ASC
                """
                cursor.execute(query, (id_tipo_periodo,))
            else:
                query = """
                    SELECT 
                        n.id, 
                        n.nombre, 
                        n.tipo, 
                        n.numero, 
                        n.duracion_semanas, 
                        n.activo,
                        n.id_tipoPeriodo, 
                        tp.nombrePeriodo
                    FROM tb_niveles_academicos n
                    LEFT JOIN tb_tipoperiodo tp ON tp.id = n.id_tipoPeriodo
                    WHERE n.activo = 1
                    ORDER BY n.id_tipoPeriodo ASC, n.numero ASC
                """
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
