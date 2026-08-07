from app.config.conexion import get_connection
import pymysql


class CursosExtraService:
    @staticmethod
    def create_curso_extracurricular(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_cursoExtracurricular (nombre,descripcion,fechaInicio,fechaFin,idCentroTrabajo,idDocente) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("nombre"),
                    data.get("descripcion"),
                    data.get("fechaInicio"),
                    data.get("fechaFin"),
                    data.get("idCentroTrabajo"),
                    data.get("idDocente"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Curso extracurricular creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_cursos_extracurriculares():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("""
                SELECT 
                    ce.id,
                    ce.nombre,
                    ce.descripcion,
                    ce.fechaInicio,
                    ce.fechaFin,
                    ct.nombre AS nombreCentroTrabajo,
                    CONCAT(d.nombreDocente, ' ', d.apPaternoDocente, ' ', d.apMaternoDocente) AS nombreDocente
                FROM tb_cursoExtracurricular ce
                LEFT JOIN tb_centrotrabajo ct ON ce.idCentroTrabajo = ct.id
                LEFT JOIN tb_docentes d ON ce.idDocente = d.idDocente
                """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
