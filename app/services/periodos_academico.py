import datetime
import pymysql
from app.config.conexion import get_connection

class PeriodoAcademicoService:

    @staticmethod
    def calcularNivelGrupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # Obtener datos del grupo sin alterar su fechaInicio ni fechaFin globales
            cursor.execute("""
                SELECT id, clave, fechaInicio, fechaFin, id_tipoPeriodo, id_nivel_academico
                FROM tb_grupos
                WHERE id = %s
            """, (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return None

            fecha_inicio_absoluta = grupo["fechaInicio"]
            id_tipo_periodo = grupo["id_tipoPeriodo"]
            id_nivel_actual_db = grupo["id_nivel_academico"]

            # Fallback en caso de que id_tipoPeriodo o el nivel actual no estén definidos
            if id_tipo_periodo is None:
                if id_nivel_actual_db is not None and id_nivel_actual_db >= 11:
                    id_tipo_periodo = 1  # SEMESTRAL
                else:
                    id_tipo_periodo = 2  # TRIMESTRAL (default)

            # Determinar el nivel inicial
            if id_tipo_periodo == 2:
                id_nivel = 1   # 1er Trimestre
            elif id_tipo_periodo == 1:
                id_nivel = 11  # 1er Semestre
            else:
                id_nivel = 1

            fecha_inicio_nivel = fecha_inicio_absoluta
            today = datetime.date.today()
            fecha_fin_nivel = fecha_inicio_nivel

            while True:
                # Obtener la duración en semanas del nivel actual
                cursor.execute("""
                    SELECT duracionSemanas 
                    FROM tb_niveles_academicos 
                    WHERE id = %s
                """, (id_nivel,))
                nivel_row = cursor.fetchone()
                
                if not nivel_row:
                    break

                duracion_semanas = nivel_row["duracionSemanas"]
                
                # Todos los periodos duran exactamente (weeks - 1) * 7 días inclusive (por ejemplo, de Domingo a Domingo)
                fecha_fin_nivel = fecha_inicio_nivel + datetime.timedelta(weeks=duracion_semanas - 1)

                # Si hoy se encuentra dentro del rango de este nivel, hemos encontrado el actual
                if today <= fecha_fin_nivel:
                    break

                next_id_nivel = id_nivel + 1
                
                # Validar que el siguiente nivel exista en la base de datos
                cursor.execute("SELECT id FROM tb_niveles_academicos WHERE id = %s", (next_id_nivel,))
                if not cursor.fetchone():
                    break

                # El siguiente periodo empieza una semana después del fin del actual (día de la siguiente clase)
                fecha_inicio_nivel = fecha_fin_nivel + datetime.timedelta(weeks=1)
                id_nivel = next_id_nivel

            cambio = (id_nivel != id_nivel_actual_db)

            return {
                "id_grupo": id_grupo,
                "id_nivel_academico": id_nivel,
                "fechaInicioNivel": fecha_inicio_nivel,
                "fechaFinNivel": fecha_fin_nivel,
                "cambiado": cambio
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizarNivelGrupo(id_grupo):
        result = PeriodoAcademicoService.calcularNivelGrupo(id_grupo)
        if not result or not result["cambiado"]:
            return False

        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # ÚNICAMENTE actualizamos el id_nivel_academico. Las fechas del grupo quedan intactas.
            cursor.execute("""
                UPDATE tb_grupos
                SET id_nivel_academico = %s
                WHERE id = %s
            """, (
                result["id_nivel_academico"],
                id_grupo
            ))
            conexion.commit()
            return True
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizarTodosLosGrupos():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT id FROM tb_grupos")
            grupos = cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

        actualizados = 0
        for g in grupos:
            if PeriodoAcademicoService.actualizarNivelGrupo(g["id"]):
                actualizados += 1
        return actualizados