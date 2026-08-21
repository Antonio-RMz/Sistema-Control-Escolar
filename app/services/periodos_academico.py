import datetime
import pymysql
from app.config.conexion import get_connection

class PeriodoAcademicoService:

    @staticmethod
    def get_active_level_for_date(group_start_date, group_end_date, id_tipo_periodo, id_nivel_actual_db, eval_date):
        if eval_date is None:
            return id_nivel_actual_db or 1
            
        if isinstance(eval_date, datetime.datetime):
            eval_date = eval_date.date()
        if isinstance(group_start_date, datetime.datetime):
            group_start_date = group_start_date.date()
        if isinstance(group_end_date, datetime.datetime):
            group_end_date = group_end_date.date()
            
        if id_tipo_periodo is None:
            if id_nivel_actual_db is not None and id_nivel_actual_db >= 7:
                id_tipo_periodo = 1  # SEMESTRAL
            else:
                id_tipo_periodo = 2  # TRIMESTRAL
                
        if id_tipo_periodo == 1:
            # For Semestral (BTI / Escolarizado), the group's level is static
            return id_nivel_actual_db or 7
            
        # For Trimestral (modular progression)
        start_level = 1
        max_level = 6
        weeks_per_level = 13
            
        for lvl in range(start_level, max_level + 1):
            offset_weeks = (lvl - start_level) * weeks_per_level
            lvl_start = group_start_date + datetime.timedelta(weeks=offset_weeks)
            lvl_end = lvl_start + datetime.timedelta(weeks=weeks_per_level - 1)
            
            # Cap at group end date
            if group_end_date:
                if lvl_start > group_end_date:
                    lvl_start = group_end_date
                if lvl_end > group_end_date:
                    lvl_end = group_end_date
                    
            if lvl_start <= eval_date <= lvl_end:
                return lvl
                
        return id_nivel_actual_db or start_level

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
                if id_nivel_actual_db is not None and id_nivel_actual_db >= 7:
                    id_tipo_periodo = 1  # SEMESTRAL
                else:
                    id_tipo_periodo = 2  # TRIMESTRAL (default)

            # Determinar el nivel inicial
            if id_tipo_periodo == 2:
                id_nivel = 1   # 1er Trimestre
            elif id_tipo_periodo == 1:
                id_nivel = 7  # 1er Semestre
            else:
                id_nivel = 1

            fecha_inicio_nivel = fecha_inicio_absoluta
            today = datetime.date.today()
            fecha_fin_nivel = fecha_inicio_nivel

            while True:
                # Obtener la duración en semanas del nivel actual
                cursor.execute("""
                    SELECT duracion_semanas 
                    FROM tb_niveles_academicos 
                    WHERE id = %s
                """, (id_nivel,))
                nivel_row = cursor.fetchone()
                
                if not nivel_row:
                    break

                duracion_semanas = nivel_row["duracion_semanas"]
                
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

            # Solo permitir avance automático de nivel, nunca retroceso/downgrade
            # para no sobrescribir la configuración manual del usuario
            if id_nivel_actual_db is not None:
                cambio = (id_nivel > id_nivel_actual_db)
            else:
                cambio = True

            # Capping at group's official fechaFin
            fecha_fin_absoluta = grupo["fechaFin"]
            if fecha_fin_absoluta:
                if isinstance(fecha_fin_absoluta, datetime.datetime):
                    fecha_fin_absoluta = fecha_fin_absoluta.date()
                if isinstance(fecha_inicio_nivel, datetime.datetime):
                    fecha_inicio_nivel = fecha_inicio_nivel.date()
                if isinstance(fecha_fin_nivel, datetime.datetime):
                    fecha_fin_nivel = fecha_fin_nivel.date()
                
                if fecha_fin_nivel > fecha_fin_absoluta:
                    fecha_fin_nivel = fecha_fin_absoluta
                if fecha_inicio_nivel > fecha_fin_absoluta:
                    fecha_inicio_nivel = fecha_fin_absoluta

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
            # ÚNICAMENTE actualizamos los grupos que estén activos
            cursor.execute("SELECT id FROM tb_grupos WHERE statusGrupo = 'ACTIVO'")
            grupos = cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

        actualizados = 0
        for g in grupos:
            if PeriodoAcademicoService.actualizarNivelGrupo(g["id"]):
                actualizados += 1
        return actualizados