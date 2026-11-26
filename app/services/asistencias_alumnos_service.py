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

            if id_tipo_periodo == 1:
                # Grupos semestrales (BTI): todas las fechas de clase pertenecen al semestre activo del grupo
                active_lvl = grupo.get("active_level") or grupo.get("id_nivel_academico") or 7
                cursor.execute("SELECT id, nombre, numero FROM tb_niveles_academicos WHERE id = %s", (active_lvl,))
                lvl_info = cursor.fetchone()
                if not lvl_info:
                    sem_num = active_lvl - 6 if active_lvl > 6 else 1
                    lvl_info = {"id": active_lvl, "nombre": f"{sem_num}er Semestre" if sem_num in [1, 3] else (f"{sem_num}do Semestre" if sem_num == 2 else f"{sem_num}to Semestre"), "numero": sem_num}
                fechas_mapeadas = [{
                    "fecha": f.strftime("%Y-%m-%d"),
                    "id_nivel_academico": lvl_info["id"],
                    "nombreNivel": lvl_info["nombre"],
                    "numeroNivel": lvl_info["numero"]
                } for f in fechas_clase]
            else:
                # 4. Precalcular los rangos de nivel academico para el grupo (modular trimestral)
                rangos_niveles = AsistenciasAlumnosService._calcular_rangos_niveles(fecha_inicio, id_tipo_periodo, cursor)

                # 5. Mapear cada fecha de clase con su respectivo nivel academico
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
                SELECT a.idAlumno, a.nombre AS nombreAlumno, a.apPaterno AS apPaternoAlumno, a.apMaterno AS apMaternoAlumno, a.numeroControl AS matricula, ag.estado, a.statusAlumno
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO' AND a.statusAlumno = 'ACTIVO'
                ORDER BY a.apPaterno, a.apMaterno, a.nombre
            """, (id_grupo,))
            alumnos = cursor.fetchall()

            # Asegurar existencia de tabla de reaperturas
            AsistenciasAlumnosService._asegurar_tabla_reaperturas(cursor)

            # Obtener fechas con permiso de reapertura activo para docentes
            cursor.execute("""
                SELECT DISTINCT fecha 
                FROM tb_asistencias_reaperturas 
                WHERE id_grupo = %s AND habilitado = 1
            """, (id_grupo,))
            reaperturas_raw = cursor.fetchall()
            reaperturas_fechas = [
                r["fecha"].strftime("%Y-%m-%d") if hasattr(r["fecha"], "strftime") else str(r["fecha"]) 
                for r in reaperturas_raw
            ]

            # Obtener materias asociadas estrictamente al horario armado de este grupo
            # 1. Determinar si existe horario oficial armado (es_prehorario = 0)
            cursor.execute("SELECT 1 FROM tb_horarios WHERE id_grupo = %s AND es_prehorario = 0 LIMIT 1", (id_grupo,))
            tiene_horario_oficial = cursor.fetchone() is not None
            filtro_prehorario = 0 if tiene_horario_oficial else 1

            active_level = grupo.get("active_level")
            materias = []

            # 2. Si el grupo tiene nivel académico activo (ej. 4to Trimestre),
            # buscar prioritariamente las materias asignadas en el armado del horario para ese nivel
            if active_level is not None:
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
                        WHERE h.id_grupo = %s 
                          AND h.es_prehorario = %s 
                          AND (m.id_nivel_academico = %s OR m.id_nivel_academico IS NULL)
                          AND h.id_docente = %s
                        ORDER BY m.nombreMateria ASC
                    """, (id_grupo, filtro_prehorario, active_level, id_docente))
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
                          AND h.es_prehorario = %s 
                          AND (m.id_nivel_academico = %s OR m.id_nivel_academico IS NULL)
                        ORDER BY m.nombreMateria ASC
                    """, (id_grupo, filtro_prehorario, active_level))
                materias = cursor.fetchall()

            # 3. Si no hubo materias y el grupo no tiene active_level definido, buscar todas las del horario armado
            if not materias and active_level is None:
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
                        WHERE h.id_grupo = %s AND h.es_prehorario = %s AND h.id_docente = %s
                        ORDER BY m.nombreMateria ASC
                    """, (id_grupo, filtro_prehorario, id_docente))
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
                        WHERE h.id_grupo = %s AND h.es_prehorario = %s
                        ORDER BY m.nombreMateria ASC
                    """, (id_grupo, filtro_prehorario))
                materias = cursor.fetchall()

            # 4. Solamente si el grupo no tiene NINGÚN registro en tb_horarios, fallback a tb_materias
            if not materias and not tiene_horario_oficial:
                if active_level is not None:
                    cursor.execute("""
                        SELECT 
                            m.id AS idMateria,
                            m.nombreMateria,
                            m.clave AS claveMateria,
                            m.id_nivel_academico,
                            NULL AS id_docente,
                            'Sin docente asignado' AS nombreDocente
                        FROM tb_materias m
                        WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
                          AND (m.id_nivel_academico = %s OR m.id_nivel_academico IS NULL)
                        ORDER BY m.nombreMateria ASC
                    """, (grupo.get("id_centroTrabajo") or 3, active_level))
                    materias = cursor.fetchall()

                if not materias:
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
            col_origen = ", es_pase_general" if AsistenciasAlumnosService.tiene_columna_pase_general(cursor) else ""
            if id_materia and str(id_materia).lower() != 'general':
                # Pase por materia: lo que registró el docente en su clase (no el pase general)
                cursor.execute(f"""
                    SELECT id, id_alumno, fecha, id_nivel_academico, estatus, observaciones,
                           created_at, updated_at{col_origen}
                    FROM tb_asistencias_alumnos
                    WHERE id_grupo = %s AND id_materia = %s
                    {AsistenciasAlumnosService.filtro_pase_docente(cursor)}
                """, (id_grupo, id_materia))
                por_dia = {}
                for a in cursor.fetchall():
                    por_dia.setdefault((a["id_alumno"], a["fecha"]), []).append(a)
                asistencias_raw = [AsistenciasAlumnosService.resolver_fila_clase(f) for f in por_dia.values()]
            else:
                # Pase general: una marca por (alumno, día) con la regla de resolver_estatus_dia.
                # Las filas del pase de los docentes no cuentan aquí.
                cursor.execute(f"""
                    SELECT id, id_alumno, fecha, id_nivel_academico, estatus, observaciones,
                           created_at, updated_at{col_origen}
                    FROM tb_asistencias_alumnos
                    WHERE id_grupo = %s
                    {AsistenciasAlumnosService.filtro_pase_general(cursor)}
                """, (id_grupo,))
                por_dia = {}
                for a in cursor.fetchall():
                    por_dia.setdefault((a["id_alumno"], a["fecha"]), []).append(a)
                asistencias_raw = [AsistenciasAlumnosService.resolver_estatus_dia(f) for f in por_dia.values()]

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

            # Días especiales del calendario (inhábil, suspensión, en línea)
            dias_especiales = AsistenciasAlumnosService.dias_especiales_lista(
                AsistenciasAlumnosService.get_dias_especiales(cursor, id_grupo)
            )

            # Convertir fechas del grupo para serializar a JSON
            grupo["fechaInicio"] = grupo["fechaInicio"].strftime("%Y-%m-%d") if isinstance(grupo["fechaInicio"], datetime.date) else str(grupo["fechaInicio"])
            grupo["fechaFin"] = grupo["fechaFin"].strftime("%Y-%m-%d") if isinstance(grupo["fechaFin"], datetime.date) else str(grupo["fechaFin"])

            return {
                "grupo": grupo,
                "alumnos": alumnos,
                "fechas": fechas_mapeadas,
                "asistencias": asistencias_resultado,
                "materias": materias,
                "reaperturas_fechas": reaperturas_fechas,
                "dias_especiales": dias_especiales,
                "selected_materia_id": "general" if (not id_materia or str(id_materia).lower() == 'general') else id_materia
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _asegurar_tabla_reaperturas(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_asistencias_reaperturas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_grupo INT NOT NULL,
                id_materia INT NULL,
                fecha DATE NOT NULL,
                autorizado_por VARCHAR(100) NULL,
                habilitado TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_reapertura_lookup (id_grupo, fecha, habilitado)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

    # ------------------------------------------------------------------
    # Estatus del DÍA cuando hay varias filas (una por materia) con marcas distintas
    #   El pase general de Administración escribe una fila por cada materia del horario; un
    #   pase por materia (docente) sobrescribe solo la de su materia. La regla (definida por la
    #   escuela) es que el día lo decide el PASE GENERAL. tb_asistencias_alumnos.es_pase_general
    #   (scripts/2026-11-23_asistencias_origen_pase.sql) dice de dónde viene cada fila; las
    #   anteriores a esa columna quedan en NULL.
    # ------------------------------------------------------------------
    _col_pase_general = False   # solo se cachea cuando la columna ya existe

    @staticmethod
    def tiene_columna_pase_general(cursor):
        """True si ya se aplicó el script que agrega es_pase_general (sin él, todo sigue igual)."""
        if not AsistenciasAlumnosService._col_pase_general:
            cursor.execute("""
                SELECT 1 FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_asistencias_alumnos'
                  AND COLUMN_NAME = 'es_pase_general' LIMIT 1
            """)
            AsistenciasAlumnosService._col_pase_general = cursor.fetchone() is not None
        return AsistenciasAlumnosService._col_pase_general

    # ------------------------------------------------------------------
    # Dos registros independientes en tb_asistencias_alumnos (ver
    # scripts/2026-11-26_asistencias_pase_general_y_docente.sql):
    #   * PASE GENERAL (es_pase_general = 1): el que manda; es el de la boleta BTI y la matriz general.
    #   * PASE DEL DOCENTE (es_pase_general = 0): quién estuvo en cada clase de su materia. Se guarda
    #     aparte y no cambia la boleta.
    #   * Filas anteriores a la columna (NULL): origen desconocido; cuentan para ambos lados.
    # ------------------------------------------------------------------
    @staticmethod
    def filtro_pase_general(cursor, alias=""):
        """Condición SQL (' AND …') para leer solo el pase general (y las filas sin origen)."""
        if not AsistenciasAlumnosService.tiene_columna_pase_general(cursor):
            return ""
        return f" AND ({alias}es_pase_general IS NULL OR {alias}es_pase_general = 1)"

    @staticmethod
    def filtro_pase_docente(cursor, alias=""):
        """Condición SQL (' AND …') para leer solo el pase del docente (y las filas sin origen)."""
        if not AsistenciasAlumnosService.tiene_columna_pase_general(cursor):
            return ""
        return f" AND ({alias}es_pase_general IS NULL OR {alias}es_pase_general = 0)"

    @staticmethod
    def resolver_fila_clase(filas):
        """Marca de UNA clase (alumno, materia, día): manda el pase del docente; si no lo hay,
        la fila sin origen; si tampoco, la del pase general. Entre iguales, la más reciente."""
        if not filas:
            return None
        prioridad = {0: 0, None: 1, 1: 2}
        def reciente(f):
            return (f.get('updated_at') or f.get('created_at') or datetime.datetime.min, f.get('id') or 0)
        mejor = min(prioridad.get(f.get('es_pase_general'), 1) for f in filas)
        return max((f for f in filas if prioridad.get(f.get('es_pase_general'), 1) == mejor), key=reciente)

    @staticmethod
    def resolver_estatus_dia(filas):
        """Elige la fila que representa el día de un alumno.

        filas: dicts con estatus, updated_at, id y (opcional) es_pase_general.
          1. Hay filas del pase general (es_pase_general = 1): la editada más recientemente.
          2. Hay filas sin origen (capturadas antes de la columna): el estatus que tiene la
             mayoría de ellas; el pase general llena todas las materias y un pase por materia
             cambia solo una. En empate, la más reciente.
          3. Solo pase por materia: la editada más recientemente. (Las lecturas del pase general
             filtran antes las filas del docente con filtro_pase_general, así que no llegan aquí.)
        """
        if not filas:
            return None
        def reciente(f):
            return (f.get('updated_at') or f.get('created_at') or datetime.datetime.min, f.get('id') or 0)

        general = [f for f in filas if f.get('es_pase_general') == 1]
        if general:
            return max(general, key=reciente)

        sin_origen = [f for f in filas if f.get('es_pase_general') is None]
        if sin_origen:
            conteo = {}
            for f in sin_origen:
                conteo[f['estatus']] = conteo.get(f['estatus'], 0) + 1
            maximo = max(conteo.values())
            candidatas = [f for f in sin_origen if conteo[f['estatus']] == maximo]
            return max(candidatas, key=reciente)

        return max(filas, key=reciente)

    # ------------------------------------------------------------------
    # Días especiales del calendario del grupo
    #   INHABIL / SUSPENSION: no son día de clase ni falta (el pase de ese día no se cuenta).
    #   EN_LINEA: día de clase normal, impartido en línea (se pasa lista igual).
    # ------------------------------------------------------------------
    TIPOS_DIA_ESPECIAL = ("INHABIL", "SUSPENSION", "EN_LINEA")
    TIPOS_SIN_CLASE = ("INHABIL", "SUSPENSION")

    @staticmethod
    def _asegurar_tabla_dias_especiales(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_grupo_dias_especiales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_grupo INT NOT NULL,
                fecha DATE NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                motivo VARCHAR(255) NULL,
                registrado_por VARCHAR(120) NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_grupo_fecha (id_grupo, fecha),
                KEY idx_fecha (fecha)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    @staticmethod
    def get_dias_especiales(cursor, id_grupo, desde=None, hasta=None):
        """{fecha(date): {tipo, motivo, registrado_por, actualizado}} del grupo."""
        AsistenciasAlumnosService._asegurar_tabla_dias_especiales(cursor)
        sql = "SELECT fecha, tipo, motivo, registrado_por, updated_at FROM tb_grupo_dias_especiales WHERE id_grupo = %s"
        params = [id_grupo]
        if desde:
            sql += " AND fecha >= %s"
            params.append(desde)
        if hasta:
            sql += " AND fecha <= %s"
            params.append(hasta)
        cursor.execute(sql, tuple(params))
        out = {}
        for r in cursor.fetchall() or []:
            if not isinstance(r, dict):
                r = dict(zip(("fecha", "tipo", "motivo", "registrado_por", "updated_at"), r))
            f = r["fecha"]
            if isinstance(f, datetime.datetime):
                f = f.date()
            elif not isinstance(f, datetime.date):
                f = datetime.datetime.strptime(str(f)[:10], "%Y-%m-%d").date()
            upd = r.get("updated_at")
            out[f] = {
                "tipo": r["tipo"],
                "motivo": r.get("motivo") or "",
                "registrado_por": r.get("registrado_por") or "",
                "actualizado": upd.isoformat(sep=" ") if isinstance(upd, datetime.datetime) else (str(upd) if upd else None),
            }
        return out

    @staticmethod
    def dias_especiales_lista(dias):
        return [{"fecha": f.isoformat(), **d} for f, d in sorted(dias.items())]

    @staticmethod
    def guardar_dia_especial(id_grupo, fecha, tipo, motivo=None, registrado_por=None, aplicar_plantel=False):
        """
        Marca (o quita, con tipo vacío/NORMAL) un día especial del grupo.
        aplicar_plantel: aplica la misma marca a todos los grupos activos del mismo plantel
        cuyo calendario incluye la fecha (útil para feriados).
        No toca tb_asistencias_alumnos: el pase que ya exista ese día se conserva y solo deja de contarse.
        """
        tipo = (tipo or "").strip().upper()
        if tipo in ("", "NORMAL"):
            tipo = None
        if tipo is not None and tipo not in AsistenciasAlumnosService.TIPOS_DIA_ESPECIAL:
            return {"error": "Tipo de día no válido."}, 400
        motivo = (motivo or "").strip()[:255] or None
        if tipo == "SUSPENSION" and not motivo:
            return {"error": "Indica el motivo de la suspensión."}, 400
        try:
            fecha_d = datetime.datetime.strptime(str(fecha)[:10], "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Fecha inválida (use AAAA-MM-DD)."}, 400

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            AsistenciasAlumnosService._asegurar_tabla_dias_especiales(cursor)
            cursor.execute("SELECT id, id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado."}, 404

            grupos = {int(id_grupo)}
            if aplicar_plantel:
                cursor.execute("""
                    SELECT id FROM tb_grupos
                    WHERE id_centroTrabajo = %s AND statusGrupo = 'ACTIVO'
                      AND fechaInicio <= %s AND fechaFin >= %s
                """, (grupo["id_centroTrabajo"], fecha_d, fecha_d))
                grupos |= {int(r["id"]) for r in cursor.fetchall() or []}

            for gid in sorted(grupos):
                if tipo is None:
                    cursor.execute("DELETE FROM tb_grupo_dias_especiales WHERE id_grupo = %s AND fecha = %s", (gid, fecha_d))
                else:
                    cursor.execute("""
                        INSERT INTO tb_grupo_dias_especiales (id_grupo, fecha, tipo, motivo, registrado_por)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE tipo = VALUES(tipo), motivo = VALUES(motivo), registrado_por = VALUES(registrado_por)
                    """, (gid, fecha_d, tipo, motivo, registrado_por))
            conexion.commit()
            return {
                "success": True,
                "fecha": fecha_d.isoformat(),
                "tipo": tipo,
                "motivo": motivo or "",
                "grupos_afectados": len(grupos),
            }
        except Exception as e:
            conexion.rollback()
            return {"error": f"No se pudo guardar el día: {e}"}, 500
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def reabrir_pase(id_grupo, fecha, id_materia=None, autorizado_por=None, habilitar=True):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            AsistenciasAlumnosService._asegurar_tabla_reaperturas(cursor)
            mat_id = int(id_materia) if (id_materia and str(id_materia).lower() != 'general') else None
            
            if habilitar:
                cursor.execute("""
                    INSERT INTO tb_asistencias_reaperturas 
                    (id_grupo, id_materia, fecha, autorizado_por, habilitado)
                    VALUES (%s, %s, %s, %s, 1)
                """, (id_grupo, mat_id, fecha, autorizado_por))
            else:
                cursor.execute("""
                    UPDATE tb_asistencias_reaperturas 
                    SET habilitado = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id_grupo = %s AND fecha = %s
                """, (id_grupo, fecha))
            
            conexion.commit()
            return {
                "success": True, 
                "habilitado": bool(habilitar), 
                "mensaje": f"Permiso de pase de lista {'habilitado' if habilitar else 'bloqueado'} correctamente para el docente."
            }
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_asistencias(id_grupo, asistencias_list, id_materia=None, id_docente=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            AsistenciasAlumnosService._asegurar_tabla_reaperturas(cursor)
            hoy_str = datetime.date.today().strftime("%Y-%m-%d")

            es_general = (not id_materia or str(id_materia).lower() == 'general')
            mat_id_int = None if es_general else int(id_materia)

            # Días inhábiles o de suspensión: no hay clase, no se registra asistencia
            sin_clase = {
                f.isoformat() for f, d in AsistenciasAlumnosService.get_dias_especiales(cursor, id_grupo).items()
                if d["tipo"] in AsistenciasAlumnosService.TIPOS_SIN_CLASE
            }
            omitidas = sorted({str(a.get("fecha"))[:10] for a in asistencias_list if str(a.get("fecha"))[:10] in sin_clase})
            asistencias_list = [a for a in asistencias_list if str(a.get("fecha"))[:10] not in sin_clase]

            fechas_en_lista = sorted(list(set(str(a.get("fecha")) for a in asistencias_list if a.get("fecha"))))
            if not fechas_en_lista:
                if omitidas:
                    return {"mensaje": "No se guardó nada: las fechas enviadas están marcadas como día inhábil o suspensión."}
                return {"mensaje": "No se recibieron registros para guardar."}

            # Pase general y pase del docente son registros separados: cada uno revisa y borra solo los suyos.
            # El docente solo cuenta como "ya enviado" su propio pase (con origen 0), no el pase general.
            tiene_origen = AsistenciasAlumnosService.tiene_columna_pase_general(cursor)
            propio = "" if not tiene_origen else (
                " AND (es_pase_general IS NULL OR es_pase_general = 1)" if es_general else " AND es_pase_general = 0")

            # Si es docente, verificar si el pase de lista para las fechas enviadas ya fue cerrado previamente
            if id_docente:
                for f_target in fechas_en_lista:
                    if not es_general:
                        cursor.execute(f"""
                            SELECT 1 FROM tb_asistencias_alumnos 
                            WHERE id_grupo = %s AND id_materia = %s AND fecha = %s AND estatus IS NOT NULL AND estatus != ''
                            {propio}
                            LIMIT 1
                        """, (id_grupo, mat_id_int, f_target))
                    else:
                        cursor.execute(f"""
                            SELECT 1 FROM tb_asistencias_alumnos 
                            WHERE id_grupo = %s AND fecha = %s AND estatus IS NOT NULL AND estatus != ''
                            {propio}
                            LIMIT 1
                        """, (id_grupo, f_target))
                    ya_enviado = cursor.fetchone() is not None

                    if ya_enviado:
                        # Validar si administración otorgó permiso de reapertura para esta fecha
                        if not es_general:
                            cursor.execute("""
                                SELECT 1 FROM tb_asistencias_reaperturas 
                                WHERE id_grupo = %s AND fecha = %s AND habilitado = 1
                                  AND (id_materia IS NULL OR id_materia = 0 OR id_materia = %s)
                                LIMIT 1
                            """, (id_grupo, f_target, mat_id_int))
                        else:
                            cursor.execute("""
                                SELECT 1 FROM tb_asistencias_reaperturas 
                                WHERE id_grupo = %s AND fecha = %s AND habilitado = 1
                                LIMIT 1
                            """, (id_grupo, f_target))
                        reapertura_activa = cursor.fetchone() is not None

                        if not reapertura_activa:
                            return {
                                "error": f"El pase de lista para la fecha {f_target} ya fue enviado previamente y se encuentra cerrado. Para realizar modificaciones, solicita la reapertura a la administración."
                            }, 403
            
            # Origen de la fila (pase general = 1, pase por materia = 0): con él la matriz y la
            # boleta saben qué marca manda en el día (ver resolver_estatus_dia).
            if AsistenciasAlumnosService.tiene_columna_pase_general(cursor):
                origen = "1" if es_general else "0"
                col_origen, val_origen, upd_origen = ", es_pase_general", f", {origen}", f"es_pase_general = {origen},"
            else:
                col_origen = val_origen = upd_origen = ""
            query = f"""
                INSERT INTO tb_asistencias_alumnos
                (id_alumno, id_materia, id_docente, id_grupo, fecha, id_nivel_academico, estatus, observaciones{col_origen})
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s{val_origen})
                ON DUPLICATE KEY UPDATE
                    {upd_origen}
                    estatus = VALUES(estatus),
                    id_nivel_academico = VALUES(id_nivel_academico),
                    observaciones = VALUES(observaciones),
                    id_docente = VALUES(id_docente)
            """

            if es_general:
                # Obtener materias y docentes del grupo desde el horario armado oficial
                cursor.execute("SELECT 1 FROM tb_horarios WHERE id_grupo = %s AND es_prehorario = 0 LIMIT 1", (id_grupo,))
                tiene_oficial = cursor.fetchone() is not None
                filtro_pre = 0 if tiene_oficial else 1

                cursor.execute("""
                    SELECT DISTINCT h.id_materia, h.id_docente, m.id_nivel_academico 
                    FROM tb_horarios h
                    JOIN tb_materias m ON h.id_materia = m.id
                    WHERE h.id_grupo = %s AND h.es_prehorario = %s
                """, (id_grupo, filtro_pre))
                horarios = cursor.fetchall()
                if not horarios:
                    cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
                    grp = cursor.fetchone()
                    cct = (grp.get("id_centroTrabajo") if isinstance(grp, dict) else grp[0]) if grp else 3
                    cursor.execute("""
                        SELECT id AS id_materia, 1 AS id_docente, id_nivel_academico 
                        FROM tb_materias 
                        WHERE idCentroTrabajo = %s OR idCentroTrabajo IS NULL
                    """, (cct,))
                    horarios = cursor.fetchall()

                for a in asistencias_list:
                    id_alumno = a.get("id_alumno")
                    fecha = a.get("fecha")
                    id_nivel = a.get("id_nivel_academico")
                    estatus = a.get("estatus")
                    obs = a.get("observaciones") or None

                    if estatus is None or estatus == "":
                        cursor.execute(f"DELETE FROM tb_asistencias_alumnos WHERE id_grupo = %s AND id_alumno = %s AND fecha = %s{propio}", (id_grupo, id_alumno, fecha))
                    elif estatus in ('A', 'F', 'R', 'J'):
                        for h in horarios:
                            m_id = h.get("id_materia") if isinstance(h, dict) else h[0]
                            d_id = (h.get("id_docente") if isinstance(h, dict) else h[1]) or 1
                            n_id = id_nivel or (h.get("id_nivel_academico") if isinstance(h, dict) else h[2])
                            cursor.execute(query, (id_alumno, m_id, d_id, id_grupo, fecha, n_id, estatus, obs))
            else:
                # Fallback de docente desde horarios si no viene provisto
                if not id_docente and id_materia:
                    cursor.execute("""
                        SELECT id_docente 
                        FROM tb_horarios 
                        WHERE id_grupo = %s AND id_materia = %s 
                        ORDER BY es_prehorario ASC
                        LIMIT 1
                    """, (id_grupo, id_materia))
                    row = cursor.fetchone()
                    if row:
                        id_docente = row.get("id_docente") if isinstance(row, dict) else row[0]

                if not id_docente:
                    id_docente = 1

                for a in asistencias_list:
                    id_alumno = a.get("id_alumno")
                    fecha = a.get("fecha")
                    id_nivel = a.get("id_nivel_academico")
                    estatus = a.get("estatus")
                    obs = a.get("observaciones") or None

                    if estatus is None or estatus == "":
                        cursor.execute(f"DELETE FROM tb_asistencias_alumnos WHERE id_grupo = %s AND id_materia = %s AND id_alumno = %s AND fecha = %s{propio}", (id_grupo, id_materia, id_alumno, fecha))
                    elif estatus in ('A', 'F', 'R', 'J'):
                        cursor.execute(query, (id_alumno, id_materia, id_docente, id_grupo, fecha, id_nivel, estatus, obs))

            # Si el docente completó y guardó su pase de lista, consumir la reapertura para que vuelva a quedar cerrado
            if id_docente:
                for f_target in fechas_en_lista:
                    if not es_general:
                        cursor.execute("""
                            UPDATE tb_asistencias_reaperturas 
                            SET habilitado = 0, updated_at = CURRENT_TIMESTAMP
                            WHERE id_grupo = %s AND fecha = %s AND habilitado = 1
                              AND (id_materia IS NULL OR id_materia = 0 OR id_materia = %s)
                        """, (id_grupo, f_target, mat_id_int))
                    else:
                        cursor.execute("""
                            UPDATE tb_asistencias_reaperturas 
                            SET habilitado = 0, updated_at = CURRENT_TIMESTAMP
                            WHERE id_grupo = %s AND fecha = %s AND habilitado = 1
                        """, (id_grupo, f_target))

            conexion.commit()
            return {"mensaje": "Asistencias guardadas correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": f"Error al guardar asistencias: {str(e)}"}, 500
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

    @staticmethod
    def _format_time(val):
        if val is None:
            return '--:--'
        if isinstance(val, datetime.timedelta):
            total_seconds = int(val.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f'{hours:02d}:{minutes:02d}'
        if isinstance(val, (datetime.time, datetime.datetime)):
            return val.strftime('%H:%M')
        return str(val)[:5]

    @staticmethod
    def get_reporte_grupo(id_grupo):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Grupo
            cursor.execute('''
                SELECT id, clave, horario, modalidadHorario, id_centroTrabajo
                FROM tb_grupos
                WHERE id = %s
            ''', (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {'error': 'Grupo no encontrado'}, 404

            # 2. Alumnos inscritos activos
            cursor.execute('''
                SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO'
                ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
            ''', (id_grupo,))
            alumnos = cursor.fetchall()
            if not alumnos:
                cursor.execute('''
                    SELECT idAlumno, nombre, apPaterno, apMaterno, numeroControl
                    FROM tb_alumnos
                    WHERE idGrupo = %s AND (statusAlumno IS NULL OR statusAlumno NOT IN ('BAJA_DEFINITIVA', 'INACTIVO'))
                    ORDER BY apPaterno ASC, apMaterno ASC, nombre ASC
                ''', (id_grupo,))
                alumnos = cursor.fetchall()

            # 3. Materias del horario
            cursor.execute('''
                SELECT DISTINCT m.id AS id_materia, m.nombreMateria, m.clave, h.id_docente,
                       TRIM(CONCAT_WS(' ', d.nombreDocente, COALESCE(d.apPaternoDocente, ''), COALESCE(d.apMaternoDocente, ''))) AS docente_nombre
                FROM tb_horarios h
                JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s AND h.es_prehorario = 0
                ORDER BY m.nombreMateria ASC
            ''', (id_grupo,))
            materias = cursor.fetchall()

            if not materias:
                cursor.execute('''
                    SELECT id AS id_materia, nombreMateria, clave, NULL AS id_docente, 'Sin docente asignado' AS docente_nombre
                    FROM tb_materias
                    WHERE idCentroTrabajo = %s OR idCentroTrabajo IS NULL
                    ORDER BY nombreMateria ASC
                ''', (grupo.get('id_centroTrabajo'),))
                materias = cursor.fetchall()

            # 4. Estadisticas por materia: una marca por clase (alumno, materia, día).
            #    Manda el pase del docente; sin él, el pase general (ver resolver_fila_clase).
            col_origen = ", es_pase_general" if AsistenciasAlumnosService.tiene_columna_pase_general(cursor) else ""
            cursor.execute(f'''
                SELECT id, id_alumno, id_materia, fecha, estatus, created_at, updated_at{col_origen}
                FROM tb_asistencias_alumnos
                WHERE id_grupo = %s
            ''', (id_grupo,))
            por_clase = {}
            for r in cursor.fetchall():
                por_clase.setdefault((r['id_alumno'], r['id_materia'], r['fecha']), []).append(r)
            stats_map = {}
            for (_, id_mat, _), filas in por_clase.items():
                r = AsistenciasAlumnosService.resolver_fila_clase(filas)
                st = stats_map.setdefault(id_mat, {'total_a': 0, 'total_f': 0, 'total_r': 0, 'total_j': 0, 'total_registros': 0})
                clave = {'A': 'total_a', 'F': 'total_f', 'R': 'total_r', 'J': 'total_j'}.get(r['estatus'])
                if clave:
                    st[clave] += 1
                st['total_registros'] += 1

            reporte_materias = []
            for mat in materias:
                s = stats_map.get(mat['id_materia'], {})
                tot_a = int(s.get('total_a') or 0)
                tot_f = int(s.get('total_f') or 0)
                tot_r = int(s.get('total_r') or 0)
                tot_j = int(s.get('total_j') or 0)
                tot_reg = int(s.get('total_registros') or 0)

                valid_denom = tot_a + tot_r + tot_f
                if valid_denom > 0:
                    pct = round(((tot_a + tot_r) / valid_denom) * 100, 1)
                elif tot_reg == 0:
                    pct = None
                else:
                    pct = 100.0

                docente_name = mat.get('docente_nombre')
                if not docente_name:
                    docente_name = 'Sin docente asignado'

                reporte_materias.append({
                    'id_materia': mat['id_materia'],
                    'nombreMateria': mat['nombreMateria'],
                    'clave': mat.get('clave') or '',
                    'docente_nombre': docente_name,
                    'asistencias': tot_a,
                    'faltas': tot_f,
                    'retardos': tot_r,
                    'justificadas': tot_j,
                    'total_registros': tot_reg,
                    'porcentaje': pct
                })

            return {
                'success': True,
                'grupo': {
                    'id': grupo['id'],
                    'clave': grupo.get('clave') or '',
                    'horario': grupo.get('horario') or '',
                    'modalidad': grupo.get('modalidadHorario') or ''
                },
                'alumnos': [
                    {
                        'idAlumno': al['idAlumno'],
                        'nombre': al.get('nombre') or '',
                        'apPaterno': al.get('apPaterno') or '',
                        'apMaterno': al.get('apMaterno') or '',
                        'numeroControl': al.get('numeroControl') or ''
                    }
                    for al in alumnos
                ],
                'materias_reporte': reporte_materias
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_historial_alumno(id_grupo, id_alumno):
        dias_nombre = {
            1: 'Lunes',
            2: 'Martes',
            3: 'Miércoles',
            4: 'Jueves',
            5: 'Viernes',
            6: 'Sábado',
            7: 'Domingo'
        }
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Alumno
            cursor.execute('''
                SELECT idAlumno, nombre, apPaterno, apMaterno, numeroControl
                FROM tb_alumnos
                WHERE idAlumno = %s
            ''', (id_alumno,))
            alumno = cursor.fetchone()
            if not alumno:
                return {'error': 'Alumno no encontrado'}, 404

            # 2. Fechas unicas de asistencias registradas para este grupo
            cursor.execute('''
                SELECT DISTINCT fecha
                FROM tb_asistencias_alumnos
                WHERE id_grupo = %s
                ORDER BY fecha DESC
            ''', (id_grupo,))
            fechas_rows = cursor.fetchall()
            fechas_reg = [r['fecha'] for r in fechas_rows]

            # 3. Horarios programados del grupo
            cursor.execute('''
                SELECT h.id_horario, h.diaSemana, h.horaInicio, h.horaFin, h.aula, h.id_materia,
                       m.nombreMateria, h.id_docente,
                       TRIM(CONCAT_WS(' ', d.nombreDocente, COALESCE(d.apPaternoDocente, ''), COALESCE(d.apMaternoDocente, ''))) AS docente_nombre
                FROM tb_horarios h
                JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s AND h.es_prehorario = 0
                ORDER BY h.horaInicio ASC
            ''', (id_grupo,))
            horarios_grupo = cursor.fetchall()

            # 4. Asistencias del alumno agrupadas por fecha: una marca por clase (manda el pase del docente)
            col_origen = ", es_pase_general" if AsistenciasAlumnosService.tiene_columna_pase_general(cursor) else ""
            cursor.execute(f'''
                SELECT id, id_materia, id_docente, fecha, estatus, observaciones, created_at, updated_at{col_origen}
                FROM tb_asistencias_alumnos
                WHERE id_grupo = %s AND id_alumno = %s
            ''', (id_grupo, id_alumno))
            por_clase = {}
            for r in cursor.fetchall():
                por_clase.setdefault((r['id_materia'], r['fecha']), []).append(r)
            asistencias_raw = [AsistenciasAlumnosService.resolver_fila_clase(f) for f in por_clase.values()]
            asistencias_alumno = {}
            for a in asistencias_raw:
                f_str = a['fecha'].strftime('%Y-%m-%d') if isinstance(a['fecha'], (datetime.date, datetime.datetime)) else str(a['fecha'])
                if f_str not in asistencias_alumno:
                    asistencias_alumno[f_str] = []
                asistencias_alumno[f_str].append(a)

            # 5. Armar historial
            historial = []
            for fecha_val in fechas_reg:
                f_date = fecha_val if isinstance(fecha_val, (datetime.date, datetime.datetime)) else datetime.datetime.strptime(str(fecha_val), '%Y-%m-%d').date()
                f_str = f_date.strftime('%Y-%m-%d')
                day_of_week = f_date.isoweekday()

                clases_del_dia = [h for h in horarios_grupo if int(h.get('diaSemana') or 0) == day_of_week]
                asist_dia = asistencias_alumno.get(f_str, [])

                clases_list = []
                for clase in clases_del_dia:
                    reg = next((x for x in asist_dia if int(x['id_materia']) == int(clase['id_materia'])), None)
                    estatus = reg['estatus'] if reg and reg.get('estatus') else 'SIN_REGISTRO'
                    obs = reg['observaciones'] if reg and reg.get('observaciones') else ''

                    doc_name = clase.get('docente_nombre')
                    if not doc_name:
                        doc_name = 'Sin docente asignado'

                    clases_list.append({
                        'horaInicio': AsistenciasAlumnosService._format_time(clase.get('horaInicio')),
                        'horaFin': AsistenciasAlumnosService._format_time(clase.get('horaFin')),
                        'nombreMateria': clase.get('nombreMateria') or '',
                        'docente_nombre': doc_name,
                        'aula': clase.get('aula') or 'Sin aula',
                        'estatus': estatus,
                        'observaciones': obs
                    })

                # Si no hay clases del dia programadas pero hay asistencias
                if not clases_del_dia and asist_dia:
                    for reg in asist_dia:
                        cursor.execute('SELECT nombreMateria FROM tb_materias WHERE id = %s', (reg['id_materia'],))
                        mat_row = cursor.fetchone()
                        mat_name = mat_row['nombreMateria'] if mat_row else 'Materia Desconocida'

                        cursor.execute('''
                            SELECT TRIM(CONCAT_WS(' ', nombreDocente, COALESCE(apPaternoDocente, ''), COALESCE(apMaternoDocente, ''))) AS nombre
                            FROM tb_docentes WHERE idDocente = %s
                        ''', (reg.get('id_docente'),))
                        doc_row = cursor.fetchone()
                        doc_name = doc_row['nombre'] if doc_row and doc_row['nombre'] else 'Sin docente asignado'

                        clases_list.append({
                            'horaInicio': '--:--',
                            'horaFin': '--:--',
                            'nombreMateria': mat_name,
                            'docente_nombre': doc_name,
                            'aula': 'Extraordinaria',
                            'estatus': reg.get('estatus') or 'SIN_REGISTRO',
                            'observaciones': reg.get('observaciones') or ''
                        })

                if clases_list:
                    historial.append({
                        'fecha': f_date.strftime('%d-%m-%Y'),
                        'dia_nombre': dias_nombre.get(day_of_week, ''),
                        'clases': clases_list
                    })

            nombre_completo = f"{alumno.get('apPaterno') or ''} {alumno.get('apMaterno') or ''} {alumno.get('nombre') or ''}".strip()
            return {
                'alumno': {
                    'idAlumno': alumno['idAlumno'],
                    'nombreCompleto': nombre_completo,
                    'numeroControl': alumno.get('numeroControl')
                },
                'historial': historial
            }
        finally:
            cursor.close()
            conn.close()
