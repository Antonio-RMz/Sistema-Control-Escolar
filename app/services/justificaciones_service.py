import datetime
import pymysql
from app.config.conexion import get_connection

class JustificacionesService:

    @staticmethod
    def crear_justificacion(id_alumno, fecha_inicio_str, fecha_fin_str, motivo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            start_date = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            
            curr = start_date
            query = """
                INSERT INTO tb_justificaciones_alumnos (id_alumno, fecha, motivo)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE motivo = VALUES(motivo)
            """
            while curr <= end_date:
                cursor.execute(query, (id_alumno, curr, motivo))
                curr += datetime.timedelta(days=1)
                
            conexion.commit()
            return {"mensaje": "Justificación registrada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar_justificacion(id_alumno, fecha_str):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                DELETE FROM tb_justificaciones_alumnos 
                WHERE id_alumno = %s AND fecha = %s
            """, (id_alumno, fecha_str))
            conexion.commit()
            return {"mensaje": "Justificación eliminada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
