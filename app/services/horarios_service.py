from app.config.conexion import get_connection
import pymysql
import datetime
from datetime import timedelta


class HorariosService:
    @staticmethod
    def create_horario_grupo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            id_grupo = data.get("id_grupo")
            diaSemana = data.get("diaSemana")
            horaInicio = data.get("horaInicio") or data.get("horainicio")
            horaFin = data.get("horaFin") or data.get("horafin")
            id_docente = data.get("id_docente")
            aula = data.get("aula")
            # Soporta tanto un arreglo de IDs en 'materias' como una sola materia 'id_materia'
            materias = data.get("materias", [])
            if not materias:
                if data.get("id_materia"):
                    materias = [data.get("id_materia")]

            if not materias or not id_docente:
                return {"error": "Faltan datos de la materia o docente"}, 400

            query = "INSERT INTO tb_horarios (id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin, aula) VALUES (%s, %s, %s, %s, %s, %s,%s)"
            
            # Insertar todas las materias para el mismo docente de forma atómica
            for id_materia in materias:
                cursor.execute(
                    query,
                    (
                        id_grupo,
                        id_materia,
                        id_docente,
                        diaSemana,
                        horaInicio,
                        horaFin,
                        aula
                    )
                )
            conexion.commit()
            return {"mensaje": "Horario de grupo creado correctamente"}
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def getHorariosGrupo(id_grupo, agrupado=False):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
                SELECT
                    h.id_horario AS id,
                    h.id_grupo,
                    h.id_materia,
                    h.id_docente,
                    h.diaSemana,
                    h.aula,
                    TIME_FORMAT(h.horaInicio, '%%H:%%i:%%s') AS horaInicio,
                    TIME_FORMAT(h.horaFin, '%%H:%%i:%%s') AS horaFin,
                    m.nombreMateria AS materia_nombre,
                    CONCAT(d.nombreDocente, ' ', d.apPaternoDocente, ' ', d.apMaternoDocente) AS docente_nombre
                FROM tb_horarios h
                LEFT JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s
                ORDER BY h.diaSemana, h.horaInicio
            """
            cursor.execute(sql, (id_grupo,))
            horarios = cursor.fetchall()

            if not agrupado:
                return horarios

            # Agrupar por día, rango de hora, docente y aula
            grouped = {}
            for h in horarios:
                key = (h["diaSemana"], h["horaInicio"], h["horaFin"], h["id_docente"], h["aula"])
                if key not in grouped:
                    grouped[key] = {
                        "diaSemana": h["diaSemana"],
                        "horaInicio": h["horaInicio"],
                        "horaFin": h["horaFin"],
                        "id_docente": h["id_docente"],
                        "docente_nombre": h["docente_nombre"],
                        "aula": h["aula"],
                        "clases": []
                    }
                grouped[key]["clases"].append({
                    "id_horario": h["id"],
                    "id_materia": h["id_materia"],
                    "materia_nombre": h["materia_nombre"],
                    "id_docente": h["id_docente"],
                    "docente_nombre": h["docente_nombre"]
                })

            return list(grouped.values())
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def validacionHorario(id_grupo, id_materia, id_docente, diaSemana, horaInicio, horaFin):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            day_map = {
                "lunes": 1, "martes": 2, "miercoles": 3, "miércoles": 3,
                "jueves": 4, "viernes": 5, "sabado": 6, "sábado": 6,
                "domingo": 7
            }
            if isinstance(diaSemana, str):
                dia_semana_val = day_map.get(diaSemana.lower(), diaSemana)
            else:
                dia_semana_val = diaSemana

            # Buscamos si el docente tiene otra clase en ese mismo día y hora en un GRUPO DIFERENTE
            cursor.execute("""
                SELECT 
                    h.id_grupo,
                    g.clave AS grupo_clave,
                    m.nombreMateria AS materia_nombre
                FROM tb_horarios h
                LEFT JOIN tb_grupos g ON h.id_grupo = g.id
                LEFT JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s
                AND h.diaSemana = %s
                AND h.horaInicio = %s
                AND h.id_grupo != %s
            """, (id_docente, dia_semana_val, horaInicio, id_grupo))
            existe_empalme = cursor.fetchone()
            
            if existe_empalme:
                return {
                    "success": False,
                    "mensaje": f"El docente ya tiene una clase asignada en el grupo '{existe_empalme['grupo_clave']}' con la materia '{existe_empalme['materia_nombre']}' en este horario."
                }
            return {
                "success": True,
                "mensaje": "El docente está disponible para ese horario."
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def deleteHorarioGrupo(id_horario):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM tb_horarios WHERE id_horario = %s", (id_horario,))
            conexion.commit()
            return {"mensaje": "Horario de grupo eliminado correctamente"}
        finally:
            cursor.close()
            conexion.close()
