from app.config.conexion import get_connection
import pymysql


class NivelesAcademicosService:
    @staticmethod
    def get_nivel_academico():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT * FROM tb_niveles_academicos")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
