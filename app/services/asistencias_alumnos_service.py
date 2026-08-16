import datetime
import pymysql
from app.config.conexion import get_connection

class AsistenciasAlumnosService:

    @staticmethod
    def get_asistencias_grupo(id_grupo, id_materia=None, id_docente=None):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # 1. Obtener datos del grupo
            cursor.execute("""
                SELECT g.id, g.clave, g.fechaInicio, g.fechaFin, g.id_tipoPeriodo, g.id_nivel_academico, g.id_centroTrabajo, g.idGeneracion,
                       ct.nombre AS nombreCentroTrabajo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                WHERE g.id = %s
            """, (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado"}

            # Obtener nivel académico activo de tb_grupo_periodos_captura o tb_grupos
            cursor.execute("SELECT id_nivel_academico FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
            config_periodo = cursor.fetchone()
            if config_periodo and config_periodo.get("id_nivel_academico") is not None:
                grupo["active_level"] = config_periodo["id_nivel_academico"]
            else:
                grupo["active_level"] = grupo.get("id_nivel_academico")

            fecha_inicio = grupo["fechaInicio"]
            fecha_fin = grupo["fechaFin"]
            id_tipo_periodo = grupo["id_tipoPeriodo"]

            # Fallback de tipo de periodo si es nulo
            if id_tipo_periodo is None:
                if grupo["id_nivel_academico"] is not None and grupo["id_nivel_academico"] >= 7:
                    id_tipo_periodo = 1 # SEMESTRAL
                else:
                    id_tipo_periodo = 2 # TRIMESTRAL

            # 2. Obtener días de clase del grupo
            cursor.execute("SELECT dia FROM tb_grupodias WHERE idGrupo = %s", (id_grupo,))
            dias_filas = cursor.fetchall()
            dias_clase = [d["dia"] for d in dias_filas]

            # Fallback si no hay registros en tb_grupodias
            if not dias_clase:
                modalidad = (grupo.get("modalidadHorario") or "").upper()
                if "SABADO" in modalidad or "SÁBADO" in modalidad:
                    dias_clase = ["SABADO"]
                elif "DOMINGO" in modalidad:
                    dias_clase = ["DOMINGO"]
                elif "MATUTINO" in modalidad or "VESPERTINO" in modalidad:
                    dias_clase = ["LUNES-VIERNES"]
                else:
                    clave = (grupo.get("clave") or "").upper()
                    if clave.endswith("S"):
                        dias_clase = ["SABADO"]
                    elif clave.endswith("D"):
                        dias_clase = ["DOMINGO"]
                    elif "LV" in clave or "BTI" in clave:
                        dias_clase = ["LUNES-VIERNES"]
                    else:
                        if grupo.get("id_centroTrabajo") == 2:
                            dias_clase = ["LUNES-VIERNES"]
                        else:
                            dias_clase = ["SABADO"]

            # 3. Generar lista de todas las fechas de clase en el rango
            fechas_clase = AsistenciasAlumnosService._generar_fechas_clase(fecha_inicio, fecha_fin, dias_clase)

            # 4. Precalcular los rangos de nivel académico para el grupo
            rangos_niveles = AsistenciasAlumnosService._calcular_rangos_niveles(fecha_inicio, id_tipo_periodo, cursor)

            # 5. Mapear cada fecha de clase con su respectivo nivel académico
            fechas_mapeadas = []
            for f in fechas_clase:
                rango = AsistenciasAlumnosService._obtener_nivel_para_fecha(f, rangos_niveles)
                fechas_mapeadas.append({
                    "fecha": f.strftime("%Y-%m-%d"),
                    "id_nivel_academico": rango["id_nivel"],
                    "nombreNivel": rango["nombreNivel"],
                    "numeroNivel": rango["numeroNivel"]
                })

            # 6. Obtener alumnos del grupo
            cursor.execute("""
                SELECT a.idAlumno, a.nombre AS nombreAlumno, a.apPaterno AS apPaternoAlumno, a.apMaterno AS apMaternoAlumno, a.numeroControl AS matricula, ag.estado
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO'
                ORDER BY a.apPaterno, a.apMaterno, a.nombre
            """, (id_grupo,))
            alumnos = cursor.fetchall()

            # Obtener materias asociadas a este grupo (filtrado por docente si aplica)
            if id_docente:
                cursor.execute("""
                    SELECT DISTINCT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        h.id_docente,
                        CONCAT_WS(' ', d.nombreDocente, COALESCE(d.apPaternoDocente, ''), COALESCE(d.apMaternoDocente, '')) AS nombreDocente
                    FROM tb_horarios h
                    JOIN tb_materias m ON h.id_materia = m.id
                    LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                    WHERE h.id_grupo = %s AND h.id_docente = %s
                    ORDER BY m.nombreMateria ASC
                """, (id_grupo, id_docente))
            else:
                cursor.execute("""
                    SELECT DISTINCT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        h.id_docente,
                        CONCAT_WS(' ', d.nombreDocente, COALESCE(d.apPaternoDocente, ''), COALESCE(d.apMaternoDocente, '')) AS nombreDocente
                    FROM tb_horarios h
                    JOIN tb_materias m ON h.id_materia = m.id
                    LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                    WHERE h.id_grupo = %s
                    ORDER BY m.nombreMateria ASC
                """, (id_grupo,))
            materias = cursor.fetchall()

            if not materias:
                # Si no hay materias configuradas en tb_horarios para el grupo, traer del CCT
                cursor.execute("""
                    SELECT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        NULL AS id_docente,
                        'Sin docente asignado' AS nombreDocente
                    FROM tb_materias m
                    WHERE m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL
                    ORDER BY m.id_nivel_academico ASC, m.nombreMateria ASC
                """, (grupo.get("id_centroTrabajo") or 3,))
                materias = cursor.fetchall()

            # Asignar materia por defecto si no se pasa
            if not id_materia and materias:
                id_materia = materias[0]["idMateria"]

            # 7. Obtener pases de lista registrados para este grupo y materia
            asistencias_raw = []
            if id_materia:
                cursor.execute("""
                    SELECT id_alumno, fecha, id_nivel_academico, estatus, observaciones
                    FROM tb_asistencias_alumnos
                    WHERE id_grupo = %s AND id_materia = %s
                """, (id_grupo, id_materia))
                asistencias_raw = cursor.fetchall()

            # 8. Obtener justificaciones del administrador en el rango de fechas
            justificaciones = {}
            if alumnos:
                alumno_ids = [al["idAlumno"] for al in alumnos]
                format_strings = ','.join(['%s'] * len(alumno_ids))
                cursor.execute(f"""
                    SELECT id_alumno, fecha, motivo
                    FROM tb_justificaciones_alumnos
                    WHERE id_alumno IN ({format_strings}) AND fecha BETWEEN %s AND %s
                """, tuple(alumno_ids) + (fecha_inicio, fecha_fin))
                just_rows = cursor.fetchall()
                for jr in just_rows:
                    al_id = jr["id_alumno"]
                    fecha_str = jr["fecha"].strftime("%Y-%m-%d") if isinstance(jr["fecha"], datetime.date) else str(jr["fecha"])
                    if al_id not in justificaciones:
                        justificaciones[al_id] = {}
                    justificaciones[al_id][fecha_str] = jr["motivo"] or "Justificado por Administración"

            # Diccionario de asistencias guardadas para fácil acceso
            asistencias_map = {}
            for a in asistencias_raw:
                al_id = a["id_alumno"]
                fecha_str = a["fecha"].strftime("%Y-%m-%d") if isinstance(a["fecha"], datetime.date) else str(a["fecha"])
                if al_id not in asistencias_map:
                    asistencias_map[al_id] = {}
                asistencias_map[al_id][fecha_str] = {
                    "id_nivel_academico": a["id_nivel_academico"],
                    "estatus": a["estatus"],
                    "observaciones": a["observaciones"] or ""
                }

            # Construir el listado final de asistencias
            asistencias_resultado = []
            for f in fechas_mapeadas:
                fecha_str = f["fecha"]
                id_nivel = f["id_nivel_academico"]
                for al in alumnos:
                    al_id = al["idAlumno"]
                    
                    has_justification = (al_id in justificaciones and fecha_str in justificaciones[al_id])
                    saved_record = asistencias_map.get(al_id, {}).get(fecha_str, None)
                    
                    estatus = None
                    observaciones = ""
                    justificado_admin = False
                    
                    if has_justification:
                        estatus = "J"
                        observaciones = justificaciones[al_id][fecha_str]
                        justificado_admin = True
                    elif saved_record:
                        estatus = saved_record["estatus"]
                        observaciones = saved_record["observaciones"]
                        
                    if estatus is not None:
                        asistencias_resultado.append({
                            "id_alumno": al_id,
                            "fecha": fecha_str,
                            "id_nivel_academico": id_nivel,
                            "estatus": estatus,
                            "observaciones": observaciones,
                            "justificado_admin": justificado_admin
                        })

            # Convertir fechas del grupo para serializar a JSON
            grupo["fechaInicio"] = grupo["fechaInicio"].strftime("%Y-%m-%d") if isinstance(grupo["fechaInicio"], datetime.date) else str(grupo["fechaInicio"])
            grupo["fechaFin"] = grupo["fechaFin"].strftime("%Y-%m-%d") if isinstance(grupo["fechaFin"], datetime.date) else str(grupo["fechaFin"])

            return {
                "grupo": grupo,
                "alumnos": alumnos,
                "fechas": fechas_mapeadas,
                "asistencias": asistencias_resultado,
                "materias": materias,
                "selected_materia_id": id_materia
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_asistencias(id_grupo, asistencias_list, id_materia=None, id_docente=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Fallback de docente desde horarios si no viene provisto
            if not id_docente and id_materia:
                cursor.execute("""
                    SELECT id_docente 
                    FROM tb_horarios 
                    WHERE id_grupo = %s AND id_materia = %s 
                    LIMIT 1
                """, (id_grupo, id_materia))
                row = cursor.fetchone()
                if row:
                    id_docente = row[0]

            # Fallback a docente por defecto si sigue vacío
            if not id_docente:
                id_docente = 1

            query = """
                INSERT INTO tb_asistencias_alumnos 
                (id_alumno, id_materia, id_docente, id_grupo, fecha, id_nivel_academico, estatus, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    estatus = VALUES(estatus),
                    id_nivel_academico = VALUES(id_nivel_academico),
                    observaciones = VALUES(observaciones),
                    id_docente = VALUES(id_docente)
            """
            for a in asistencias_list:
                id_alumno = a.get("id_alumno")
                fecha = a.get("fecha")
                id_nivel = a.get("id_nivel_academico")
                estatus = a.get("estatus")
                obs = a.get("observaciones") or None

                cursor.execute(query, (id_alumno, id_materia, id_docente, id_grupo, fecha, id_nivel, estatus, obs))

            conexion.commit()
            return {"mensaje": "Asistencias guardadas correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _generar_fechas_clase(fecha_inicio, fecha_fin, dias_clase):
        fechas = []
        if not dias_clase:
            return fechas

        target_weekdays = set()
        for d in dias_clase:
            d_upper = d.upper().strip()
            if d_upper == 'SABADO':
                target_weekdays.add(5)
            elif d_upper == 'DOMINGO':
                target_weekdays.add(6)
            elif d_upper == 'LUNES-VIERNES':
                target_weekdays.update([0, 1, 2, 3, 4])

        curr = fecha_inicio
        while curr <= fecha_fin:
            if curr.weekday() in target_weekdays:
                fechas.append(curr)
            curr += datetime.timedelta(days=1)
        return fechas

    @staticmethod
    def _calcular_rangos_niveles(fecha_inicio_absoluta, id_tipo_periodo, cursor):
        cursor.execute("""
            SELECT id, nombre, numero, duracion_semanas
            FROM tb_niveles_academicos
            WHERE id_tipoPeriodo = %s
            ORDER BY numero
        """, (id_tipo_periodo,))
        niveles = cursor.fetchall()

        rangos = []
        curr_inicio = fecha_inicio_absoluta
        for n in niveles:
            duracion = n["duracion_semanas"]
            # Cada nivel dura (semanas - 1) * 7 días inclusive
            curr_fin = curr_inicio + datetime.timedelta(weeks=duracion - 1)
            rangos.append({
                "id_nivel": n["id"],
                "nombreNivel": n["nombre"],
                "numeroNivel": n["numero"],
                "inicio": curr_inicio,
                "fin": curr_fin
            })
            curr_inicio = curr_fin + datetime.timedelta(weeks=1)
        return rangos

    @staticmethod
    def _obtener_nivel_para_fecha(fecha, rangos):
        for r in rangos:
            if r["inicio"] <= fecha <= r["fin"]:
                return r
        # Si la fecha excede todos los rangos calculados, retornamos el último rango
        if rangos:
            return rangos[-1]
        return {"id_nivel": None, "nombreNivel": "Sin periodo", "numeroNivel": 1}
