from app.config.conexion import get_connection
import pymysql
import datetime
from datetime import timedelta
from app.services.periodos_academico import PeriodoAcademicoService



class DocentesService:
    @staticmethod
    def get_docentes(page, limit, search, status):
        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            offset = (page - 1) * limit

            sql = """
                SELECT 
                    idDocente, 
                    nombreDocente, 
                    apPaternoDocente, 
                    apMaternoDocente, 
                    correoDocente, 
                    usuario,
                    IF(password IS NOT NULL AND password != '', 1, 0) AS tiene_password,
                    telefonoDocente, 
                    statusDocente, 
                    observacionesDocente,
                    nivelEstudios,
                    fechaNacimiento,
                    idBiometrico,
                    permisos_modulos,
                    colorDocente
                FROM tb_docentes
                WHERE 1=1
            """

            params = []

            #  Búsqueda
            if search:
                sql += """
                    AND (
                        nombreDocente LIKE %s OR 
                        apPaternoDocente LIKE %s OR 
                        apMaternoDocente LIKE %s
                    )
                """
                like = f"%{search}%"
                params.extend([like, like, like])

            # Filtro por status
            if status:
                sql += " AND statusDocente = %s"
                params.append(status)

            #  Paginación
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(sql, params)
            data = cursor.fetchall()

            return {"data": data, "page": page, "limit": limit}

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_docente(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validar duplicados de usuario si viene especificado
            usuario = data.get("usuario")
            if usuario:
                usuario = usuario.strip()
                cursor.execute("SELECT idDocente FROM tb_docentes WHERE usuario = %s", (usuario,))
                if cursor.fetchone():
                    return {"error": "El nombre de usuario ya está asignado a otro docente"}

            query = """
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente, nivelEstudios, fechaNacimiento, idBiometrico, usuario, password, colorDocente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                    usuario if usuario else None,
                    data.get("password") if data.get("password") else None,
                    data.get("colorDocente") or "#FFFFFF"
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente creado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update_docente(id_docente, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validar duplicados de usuario
            usuario = data.get("usuario")
            if usuario:
                usuario = usuario.strip()
                cursor.execute("SELECT idDocente FROM tb_docentes WHERE usuario = %s AND idDocente != %s", (usuario, id_docente))
                if cursor.fetchone():
                    return {"error": "El nombre de usuario ya está asignado a otro docente"}

            password = data.get("password")
            if password:
                query = """
                    UPDATE tb_docentes 
                    SET nombreDocente = %s, apPaternoDocente = %s, apMaternoDocente = %s, 
                        correoDocente = %s, telefonoDocente = %s, statusDocente = %s, 
                        observacionesDocente = %s, nivelEstudios = %s, fechaNacimiento = %s,
                        idBiometrico = %s, usuario = %s, password = %s, colorDocente = %s
                    WHERE idDocente = %s
                """
                params = (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                    usuario if usuario else None,
                    password,
                    data.get("colorDocente") or "#FFFFFF",
                    id_docente
                )
            else:
                query = """
                    UPDATE tb_docentes 
                    SET nombreDocente = %s, apPaternoDocente = %s, apMaternoDocente = %s, 
                        correoDocente = %s, telefonoDocente = %s, statusDocente = %s, 
                        observacionesDocente = %s, nivelEstudios = %s, fechaNacimiento = %s,
                        idBiometrico = %s, usuario = %s, colorDocente = %s
                    WHERE idDocente = %s
                """
                params = (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                    usuario if usuario else None,
                    data.get("colorDocente") or "#FFFFFF",
                    id_docente
                )
            cursor.execute(query, params)
            conexion.commit()
            return {"mensaje": "Docente actualizado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete_docente(idDocente):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Eliminar relaciones en tablas secundarias para evitar errores de llave foránea
            cursor.execute("DELETE FROM tb_asistencias_alumnos WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_cursoextracurricular WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_grupodocentes WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_horarios WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_materiadocente WHERE idDocente = %s", (idDocente,))
            
            # 2. Eliminar el docente
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (idDocente,))
            conexion.commit()
            return {"mensaje": "Docente eliminado correctamente"}, 200
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}, 500
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_horas_docentes(fecha_inicio_str, fecha_fin_str):
        try:
            d_inicio = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            d_fin = datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Las fechas deben tener el formato YYYY-MM-DD")

        if d_inicio > d_fin:
            raise ValueError("La fecha de inicio debe ser menor o igual a la fecha de fin")

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # 1. Obtener todos los docentes activos
            cursor.execute("""
                SELECT 
                    idDocente, 
                    CONCAT(nombreDocente, ' ', COALESCE(apPaternoDocente, ''), ' ', COALESCE(apMaternoDocente, '')) AS docente
                FROM tb_docentes
                WHERE statusDocente = 'ACTIVO'
                ORDER BY nombreDocente, apPaternoDocente, apMaternoDocente
            """)
            docentes = cursor.fetchall()

            if not docentes:
                return []

            # 2. Obtener los horarios de grupos vigentes dentro del rango solicitado
            cursor.execute("""
                SELECT 
                    h.id_docente,
                    h.diaSemana,
                    h.horaInicio,
                    h.horaFin,
                    g.clave AS clave_grupo,
                    g.fechaInicio,
                    g.fechaFin,
                    g.id_tipoPeriodo,
                    g.id_nivel_academico AS id_nivel_grupo,
                    m.id_nivel_academico AS id_nivel_materia
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                LEFT JOIN tb_materias m ON h.id_materia = m.id
                WHERE g.fechaInicio <= %s AND g.fechaFin >= %s
            """, (fecha_fin_str, fecha_inicio_str))
            horarios = cursor.fetchall()

            # Organizar horarios por docente
            horarios_por_docente = {}
            for h in horarios:
                id_doc = h['id_docente']
                if id_doc not in horarios_por_docente:
                    horarios_por_docente[id_doc] = []
                horarios_por_docente[id_doc].append(h)

            # Generar la lista de fechas en el rango
            dias_rango = []
            curr = d_inicio
            while curr <= d_fin:
                dias_rango.append(curr)
                curr += timedelta(days=1)

            resultado = []

            for doc in docentes:
                id_docente = doc['idDocente']
                docente_nombre = doc['docente'].strip()
                slots_docente = horarios_por_docente.get(id_docente, [])

                dias_reporte = []
                for d in dias_rango:
                    db_weekday = d.weekday() + 1
                    fecha_str = d.strftime("%Y-%m-%d")

                    # Filtrar horarios del docente activos en este día de la semana y vigentes en esta fecha
                    # Agrupamos por (horaInicio, horaFin) para evitar contar múltiples materias en la misma hora
                    slots_dia_map = {}
                    for h in slots_docente:
                        # Convertir fechas de mysql a date de python si vienen como datetime.date
                        h_fecha_inicio = h['fechaInicio']
                        h_fecha_fin = h['fechaFin']
                        if isinstance(h_fecha_inicio, datetime.datetime):
                            h_fecha_inicio = h_fecha_inicio.date()
                        if isinstance(h_fecha_fin, datetime.datetime):
                            h_fecha_fin = h_fecha_fin.date()

                        if h['diaSemana'] == db_weekday and h_fecha_inicio <= d <= h_fecha_fin:
                            g_tipo = h.get('id_tipoPeriodo')
                            g_nivel_db = h.get('id_nivel_grupo')
                            m_nivel_id = h.get('id_nivel_materia')
                            
                            active_lvl = PeriodoAcademicoService.get_active_level_for_date(h_fecha_inicio, h_fecha_fin, g_tipo, g_nivel_db, d)
                            if m_nivel_id is None or m_nivel_id == active_lvl:
                                key = (h['horaInicio'], h['horaFin'])
                                slots_dia_map[key] = h

                    if not slots_dia_map:
                        dias_reporte.append({
                            "fecha": fecha_str,
                            "total": 0,
                            "real": 0
                        })
                        continue

                    # Calcular total de horas
                    total_minutos = 0
                    intervals = []
                    for (start_td, end_td), h_item in slots_dia_map.items():
                        is_bti = str(h_item.get('clave_grupo', '')).upper().startswith('BTI')
                        
                        if isinstance(start_td, str):
                            h, m, s_val = map(int, start_td.split(':'))
                            start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(start_td, datetime.time):
                            start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                            
                        if isinstance(end_td, str):
                            h, m, s_val = map(int, end_td.split(':'))
                            end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(end_td, datetime.time):
                            end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)

                        diff_min = (end_td - start_td).total_seconds() / 60.0
                        # En BTI cada módulo de clase (ej. 50 min) se considera como 1 hora completa (60 min)
                        if is_bti and 40 <= diff_min <= 60:
                            diff_min = 60.0

                        total_minutos += diff_min
                        intervals.append((start_td.total_seconds() / 60.0, end_td.total_seconds() / 60.0))

                    total_horas = total_minutos / 60.0

                    # Calcular real de horas (unión de intervalos)
                    intervals.sort(key=lambda x: x[0])
                    merged = []
                    for start, end in intervals:
                        if not merged:
                            merged.append([start, end])
                        else:
                            prev_start, prev_end = merged[-1]
                            if start <= prev_end:
                                merged[-1][1] = max(prev_end, end)
                            else:
                                merged.append([start, end])
                    
                    real_minutos = sum(end - start for start, end in merged)
                    real_horas = total_horas if any(str(h_item.get('clave_grupo', '')).upper().startswith('BTI') for h_item in slots_dia_map.values()) else (real_minutos / 60.0)

                    def format_hours(h):
                        h_round = round(h, 2)
                        return int(h_round) if h_round.is_integer() else h_round

                    dias_reporte.append({
                        "fecha": fecha_str,
                        "total": format_hours(total_horas),
                        "real": format_hours(real_horas)
                    })

                resultado.append({
                    "id_docente": id_docente,
                    "docente": docente_nombre,
                    "dias": dias_reporte
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_detalle_horas_docente(id_docente, fecha_str):
        try:
            d_fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD")

        # diaSemana: 1 (Lunes) a 7 (Domingo)
        db_weekday = d_fecha.weekday() + 1

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # Consultar los horarios vigentes para el docente en este día de la semana y fecha
            # Un grupo está vigentes si g.fechaInicio <= d_fecha <= g.fechaFin
            cursor.execute("""
                SELECT 
                    m.nombreMateria AS materia,
                    g.clave AS grupo,
                    h.aula,
                    h.horaInicio,
                    h.horaFin,
                    g.fechaInicio,
                    g.fechaFin,
                    g.id_tipoPeriodo,
                    g.id_nivel_academico AS id_nivel_grupo,
                    m.id_nivel_academico AS id_nivel_materia
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s 
                  AND h.diaSemana = %s
                  AND g.fechaInicio <= %s 
                  AND g.fechaFin >= %s
                ORDER BY h.horaInicio, m.nombreMateria
            """, (id_docente, db_weekday, fecha_str, fecha_str))
            
            rows = cursor.fetchall()
            
            resultado = []
            for r in rows:
                g_start = r['fechaInicio']
                g_end = r['fechaFin']
                g_tipo = r.get('id_tipoPeriodo')
                g_nivel_db = r.get('id_nivel_grupo')
                m_nivel_id = r.get('id_nivel_materia')
                
                active_lvl = PeriodoAcademicoService.get_active_level_for_date(g_start, g_end, g_tipo, g_nivel_db, d_fecha)
                if m_nivel_id is not None and m_nivel_id != active_lvl:
                    continue
                
                start_td = r['horaInicio']
                end_td = r['horaFin']
                
                # Convertir time/timedelta/string a timedelta para calcular duracion
                if isinstance(start_td, str):
                    h, m, s_val = map(int, start_td.split(':'))
                    start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    start_str = r['horaInicio']
                elif isinstance(start_td, datetime.time):
                    start_str = start_td.strftime("%H:%M:%S")
                    start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                else: # timedelta
                    tot_sec = int(start_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    start_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                if isinstance(end_td, str):
                    h, m, s_val = map(int, end_td.split(':'))
                    end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    end_str = r['horaFin']
                elif isinstance(end_td, datetime.time):
                    end_str = end_td.strftime("%H:%M:%S")
                    end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)
                else: # timedelta
                    tot_sec = int(end_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    end_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                diff_hours = (end_td - start_td).total_seconds() / 3600.0
                
                # En BTI cada módulo de clase (ej. 50 min) se considera 1 hora completa (1.0)
                is_bti = str(r.get('grupo', '')).upper().startswith('BTI')
                if is_bti and 0.7 <= diff_hours <= 1.05:
                    diff_hours = 1.0
                
                def format_hours(h):
                    h_round = round(h, 2)
                    return int(h_round) if h_round.is_integer() else h_round

                resultado.append({
                    "materia": r['materia'],
                    "grupo": r['grupo'],
                    "aula": r['aula'],
                    "hora_inicio": start_str,
                    "hora_fin": end_str,
                    "duracion": format_hours(diff_hours)
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def actualizar_credenciales(id_docente, usuario, password_hash=None, permisos_modulos=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validar que el usuario no esté duplicado en otro docente
            cursor.execute("SELECT idDocente FROM tb_docentes WHERE usuario = %s AND idDocente != %s", (usuario, id_docente))
            dup = cursor.fetchone()
            if dup:
                return {"error": "El nombre de usuario ya está asignado a otro docente"}

            if permisos_modulos is None:
                permisos_modulos = 'horarios,pendientes,grupos'

            if password_hash:
                cursor.execute("""
                    UPDATE tb_docentes 
                    SET usuario = %s, password = %s, permisos_modulos = %s, updateAt = CURRENT_TIMESTAMP
                    WHERE idDocente = %s
                """, (usuario, password_hash, permisos_modulos, id_docente))
            else:
                cursor.execute("""
                    UPDATE tb_docentes 
                    SET usuario = %s, permisos_modulos = %s, updateAt = CURRENT_TIMESTAMP
                    WHERE idDocente = %s
                """, (usuario, permisos_modulos, id_docente))
            conexion.commit()
            return {"success": True, "mensaje": "Credenciales del docente actualizadas correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def login(usuario, password):
        """
        Verifica credenciales de docente dentro de la API (el hash no sale del backend).
        Devuelve (estado, datos): 'ok' | 'no_existe' | 'sin_password' | 'password'.
        Solo considera docentes ACTIVOS (igual que la búsqueda por usuario).
        """
        from app.utils.seguridad import verificar_password
        docente = DocentesService.get_docente_by_username(usuario, incluir_password=True)
        if not docente:
            return "no_existe", None
        hash_guardado = docente.pop("password", None)
        if not hash_guardado:
            return "sin_password", None
        if not verificar_password(password, hash_guardado):
            return "password", None
        return "ok", docente

    @staticmethod
    def get_docente_by_username(usuario, incluir_password=False):
        """Docente activo por usuario/correo/nombre.apellido. La contraseña solo se lee para el login interno."""
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            if not usuario:
                return None
            u_clean = usuario.strip()
            columna_password = "password," if incluir_password else ""
            cursor.execute(f"""
                SELECT 
                    idDocente, 
                    nombreDocente, 
                    apPaternoDocente, 
                    apMaternoDocente, 
                    correoDocente, 
                    usuario, 
                    {columna_password}
                    statusDocente,
                    permisos_modulos
                FROM tb_docentes
                WHERE (
                    LOWER(TRIM(usuario)) = LOWER(%s)
                    OR LOWER(TRIM(correoDocente)) = LOWER(%s)
                    OR REPLACE(LOWER(TRIM(usuario)), 'ñ', 'n') = REPLACE(LOWER(%s), 'ñ', 'n')
                    OR REPLACE(LOWER(TRIM(correoDocente)), 'ñ', 'n') = REPLACE(LOWER(%s), 'ñ', 'n')
                    OR LOWER(CONCAT(TRIM(nombreDocente), '.', TRIM(apPaternoDocente))) = LOWER(%s)
                    OR LOWER(CONCAT(TRIM(nombreDocente), '.', TRIM(IFNULL(apMaternoDocente, '')))) = LOWER(%s)
                    OR REPLACE(LOWER(CONCAT(TRIM(nombreDocente), '.', TRIM(apPaternoDocente))), 'ñ', 'n') = REPLACE(LOWER(%s), 'ñ', 'n')
                    OR REPLACE(LOWER(CONCAT(TRIM(nombreDocente), '.', TRIM(IFNULL(apMaternoDocente, '')))), 'ñ', 'n') = REPLACE(LOWER(%s), 'ñ', 'n')
                ) AND UPPER(TRIM(statusDocente)) = 'ACTIVO'
                LIMIT 1
            """, (u_clean, u_clean, u_clean, u_clean, u_clean, u_clean, u_clean, u_clean))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _resumen_grupos_docente(cursor, id_docente):
        """
        Grupos del docente (según su horario, sin prehorarios) para la vista de Pendientes:
        periodo en curso con su avance en el tiempo, estado de la captura (abierta / próxima / cerrada)
        y avance de captura por asignatura. Las reglas de captura son las de CalificacionesService.
        """
        from app.services.calificaciones_service import CalificacionesService as CS
        hoy = datetime.date.today()
        iso = lambda d: d.isoformat() if d else None
        ORD = {1: '1er', 2: '2do', 3: '3er', 4: '4to', 5: '5to', 6: '6to'}

        cursor.execute("""
            SELECT DISTINCT g.id, g.clave, g.id_centroTrabajo, g.fechaInicio, g.fechaFin, g.modalidadHorario,
                   g.statusGrupo, g.id_nivel_academico, g.id_tipoPeriodo, na.nombre AS nombre_nivel
            FROM tb_horarios h
            JOIN tb_grupos g ON g.id = h.id_grupo
            LEFT JOIN tb_materias m ON m.id = h.id_materia
            LEFT JOIN tb_niveles_academicos na ON na.id = g.id_nivel_academico
            WHERE h.id_docente = %s
              AND (h.es_prehorario IS NULL OR h.es_prehorario = 0)
              AND (g.statusGrupo = 'ACTIVO' OR g.fechaFin >= %s)
              -- Como en Mi Horario: solo materias del nivel (trimestre/semestre) actual del grupo
              AND (m.id_nivel_academico IS NULL OR m.id_nivel_academico = g.id_nivel_academico)
            ORDER BY g.clave
        """, (id_docente, hoy - timedelta(days=21)))
        grupos = cursor.fetchall()

        resultado = []
        for g in grupos:
            id_grupo = g['id']
            es_bgne = int(g.get('id_centroTrabajo') or 0) == 3
            ini_g = CS._a_fecha(g.get('fechaInicio'))
            fin_g = CS._a_fecha(g.get('fechaFin'))

            cursor.execute("SELECT * FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
            cfg = cursor.fetchone() or {}

            # ---- Periodo en curso (trimestre BGNE con el calendario del grupo; semestre BTI = fechas del grupo) ----
            periodo = None
            if es_bgne:
                trims = CS.trimestres_grupo(ini_g, fin_g)
                if trims:
                    # En la semana de captura se sigue mostrando el trimestre que terminó
                    t = next((x for x in trims if hoy <= x['captura_fin']), trims[-1])
                    periodo = {'nombre': f"{ORD.get(t['nivel'], t['nivel'])} trimestre", 'nivel': t['nivel'],
                               'inicio': t['inicio'], 'fin': t['fin']}
            elif ini_g:
                periodo = {'nombre': (g.get('nombre_nivel') or 'Semestre').lower(),
                           'nivel': g.get('id_nivel_academico'), 'inicio': ini_g, 'fin': fin_g or ini_g}
            if periodo:
                total_dias = max((periodo['fin'] - periodo['inicio']).days, 1)
                transcurridos = (hoy - periodo['inicio']).days
                periodo.update({
                    'estado': 'por_iniciar' if hoy < periodo['inicio'] else ('terminado' if hoy > periodo['fin'] else 'en_curso'),
                    'porcentaje': max(0, min(100, round(transcurridos * 100 / total_dias))),
                    'semanas': -(-(total_dias + 1) // 7),
                    'semana': max(1, min(-(-(total_dias + 1) // 7), transcurridos // 7 + 1)),
                    'dias_restantes': max(0, (periodo['fin'] - hoy).days),
                    'inicio': iso(periodo['inicio']), 'fin': iso(periodo['fin']),
                })

            # ---- Estado de la captura del grupo ----
            # Ventanas configuradas en "Periodos por grupo" (con fechas) y, en BGNE sin fechas, la regla automática
            NOMBRES = {'p1': 'Calificación final' if es_bgne else '1er parcial', 'p2': '2do parcial', 'p3': '3er parcial',
                       'semestral': 'Examen semestral', 'extraordinario': 'Extraordinario'}
            CAMPO = {'p1': 'parcial1', 'p2': 'parcial2', 'p3': 'parcial3', 'semestral': 'semestral', 'extraordinario': 'calificacion'}
            ventanas = []
            claves = ('p1', 'extraordinario') if es_bgne else ('p1', 'p2', 'p3', 'semestral', 'extraordinario')
            for k in claves:
                hab = cfg.get(f'{k}_habilitado')
                a, b = CS._a_fecha(cfg.get(f'{k}_fecha_inicio')), CS._a_fecha(cfg.get(f'{k}_fecha_fin'))
                if (hab is None or hab) and a and b:
                    ventanas.append({'clave': k, 'etapa': NOMBRES[k], 'inicio': a, 'fin': b})
            automatica = False
            if es_bgne and not (cfg.get('p1_fecha_inicio') or cfg.get('p1_fecha_fin')):
                automatica = True
                for t in CS.trimestres_grupo(ini_g, fin_g):
                    ventanas.append({'clave': 'p1', 'etapa': f"{ORD.get(t['nivel'], t['nivel'])} trimestre",
                                     'inicio': t['fin'], 'fin': t['captura_fin']})

            abiertas = sorted([v for v in ventanas if v['inicio'] <= hoy <= v['fin']], key=lambda v: v['fin'])
            proximas = sorted([v for v in ventanas if v['inicio'] > hoy], key=lambda v: v['inicio'])
            pasadas = sorted([v for v in ventanas if v['fin'] < hoy], key=lambda v: v['fin'])
            if cfg and cfg.get('captura_habilitada') is not None and not cfg.get('captura_habilitada'):
                captura = {'estado': 'deshabilitada'}
                ref = None
            elif abiertas:
                ref = abiertas[0]
                captura = {'estado': 'abierta', 'dias_restantes': (ref['fin'] - hoy).days}
            elif proximas:
                ref = proximas[0]
                captura = {'estado': 'proxima', 'dias_para_abrir': (ref['inicio'] - hoy).days}
            elif pasadas:
                ref = pasadas[-1]
                captura = {'estado': 'cerrada'}
            else:
                ref = None
                captura = {'estado': 'sin_fechas'}
            if ref:
                captura.update({'etapa': ref['etapa'], 'inicio': iso(ref['inicio']), 'fin': iso(ref['fin'])})
            if pasadas and captura['estado'] in ('proxima', 'abierta'):
                ult = pasadas[-1]
                captura['anterior'] = {'etapa': ult['etapa'], 'fin': iso(ult['fin'])}
            captura['automatica'] = automatica

            # Campo que mide el avance: el de la etapa abierta o la última cerrada (BTI); la calificación final (BGNE)
            ref_avance = abiertas[0] if abiertas else (pasadas[-1] if pasadas else None)
            if es_bgne:
                cond = "(c.calificacion IS NOT NULL OR c.parcial1 IS NOT NULL)"
            else:
                campo = CAMPO.get(ref_avance['clave'], 'calificacion') if ref_avance else 'calificacion'
                cond = f"c.{campo} IS NOT NULL"   # nombre de columna de una lista fija

            # ---- Alumnos y asignaturas ----
            cursor.execute("""
                SELECT COUNT(*) AS n FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO' AND a.statusAlumno = 'ACTIVO'
            """, (id_grupo,))
            total_alumnos = (cursor.fetchone() or {}).get('n') or 0

            cursor.execute("""
                SELECT DISTINCT m.id, m.nombreMateria, m.clave, m.id_nivel_academico, na.nombre AS nombre_nivel
                FROM tb_horarios h
                JOIN tb_materias m ON m.id = h.id_materia
                LEFT JOIN tb_niveles_academicos na ON na.id = m.id_nivel_academico
                WHERE h.id_docente = %s AND h.id_grupo = %s
                  AND (h.es_prehorario IS NULL OR h.es_prehorario = 0)
                  AND (m.id_nivel_academico IS NULL OR m.id_nivel_academico = %s)
                ORDER BY m.nombreMateria
            """, (id_docente, id_grupo, g.get('id_nivel_academico')))
            materias = []
            for m in cursor.fetchall():
                calificados = 0
                if total_alumnos:
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT c.idAlumno) AS n
                        FROM tb_calificaciones c
                        JOIN tb_alumnogrupo ag ON ag.idAlumno = c.idAlumno AND ag.idGrupo = %s AND ag.estado = 'ACTIVO'
                        JOIN tb_alumnos a ON a.idAlumno = c.idAlumno AND a.statusAlumno = 'ACTIVO'
                        WHERE c.idMateria = %s AND {cond}
                    """, (id_grupo, m['id']))
                    calificados = (cursor.fetchone() or {}).get('n') or 0
                permiso = CS.check_captura_permission(id_grupo, m['id'], id_docente, 'DOCENTE')
                materias.append({
                    'id': m['id'],
                    'nombre': m['nombreMateria'],
                    'clave': m['clave'],
                    'nivel': m.get('nombre_nivel'),
                    'total': total_alumnos,
                    'calificados': min(calificados, total_alumnos),
                    'porcentaje': round(min(calificados, total_alumnos) * 100 / total_alumnos) if total_alumnos else 0,
                    'bloqueado': not permiso['allowed'],
                    'motivo': None if permiso['allowed'] else permiso['reason'],
                })

            tot = sum(x['total'] for x in materias)
            cal = sum(x['calificados'] for x in materias)
            resultado.append({
                'id': id_grupo,
                'clave': g['clave'],
                'plantel': 'BGNE' if es_bgne else ('BTI' if int(g.get('id_centroTrabajo') or 0) == 2 else ''),
                'modalidad': g.get('modalidadHorario'),
                'fecha_inicio': iso(ini_g),
                'fecha_fin': iso(fin_g),
                'periodo': periodo,
                'captura': captura,
                # Qué se está midiendo en el avance (BTI: el parcial abierto o el último cerrado)
                'etapa_avance': ref_avance['etapa'] if (ref_avance and not es_bgne) else 'Calificación final',
                'materias': materias,
                'avance': {'total': tot, 'calificados': cal, 'porcentaje': round(cal * 100 / tot) if tot else 0},
            })
        return resultado

    @staticmethod
    def get_docente_pendientes(id_docente):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            hoy = datetime.date.today().strftime('%Y-%m-%d')
            proximos15_dias = (datetime.date.today() + datetime.timedelta(days=15)).strftime('%Y-%m-%d')

            # 1. Prórrogas activas
            cursor.execute("""
                SELECT 
                    p.*,
                    g.clave as clave_grupo,
                    m.nombreMateria as nombre_materia,
                    m.clave as clave_materia,
                    DATEDIFF(p.fecha_limite, %s) as dias_restantes
                FROM tb_docente_permisos_captura p
                JOIN tb_grupos g ON p.id_grupo = g.id
                JOIN tb_materias m ON p.id_materia = m.id
                JOIN tb_horarios h ON p.id_grupo = h.id_grupo 
                                   AND p.id_materia = h.id_materia 
                                   AND p.id_docente = h.id_docente
                WHERE p.id_docente = %s
                  AND p.habilitado = 1
                  AND p.fecha_limite >= %s
                ORDER BY p.fecha_limite ASC
            """, (hoy, id_docente, hoy))
            prorrogas = cursor.fetchall()

            for p in prorrogas:
                if p.get('fecha_limite'):
                    p['fecha_limite'] = str(p['fecha_limite'])
                if p.get('createAt'):
                    p['createAt'] = str(p['createAt'])
                if p.get('updateAt'):
                    p['updateAt'] = str(p['updateAt'])

            # 2. Grupos por finalizar (próximos 15 días)
            cursor.execute("""
                SELECT DISTINCT
                    g.id,
                    g.clave as clave_grupo,
                    g.fechaFin as fecha_fin,
                    DATEDIFF(g.fechaFin, %s) as dias_restantes
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s
                  AND g.statusGrupo = 'ACTIVO'
                  AND (m.id_nivel_academico IS NULL OR m.id_nivel_academico = g.id_nivel_academico)
                  AND g.fechaFin >= %s
                  AND g.fechaFin <= %s
                ORDER BY g.fechaFin ASC
            """, (hoy, id_docente, hoy, proximos15_dias))
            por_finalizar = cursor.fetchall()

            for gf in por_finalizar:
                if gf.get('fecha_fin'):
                    gf['fecha_fin'] = str(gf['fecha_fin'])

            # 3. Calificaciones pendientes por capturar
            cursor.execute("""
                SELECT DISTINCT
                    g.id as id_grupo,
                    g.clave as clave_grupo,
                    m.id as id_materia,
                    m.nombreMateria as nombre_materia,
                    m.clave as clave_materia
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s
                  AND g.statusGrupo = 'ACTIVO'
                  AND (m.id_nivel_academico IS NULL OR m.id_nivel_academico = g.id_nivel_academico)
            """, (id_docente,))
            clases = cursor.fetchall()

            calificaciones_pendientes = []

            from app.services.calificaciones_service import CalificacionesService

            for clase in clases:
                cursor.execute("""
                    SELECT ag.idAlumno FROM tb_alumnogrupo ag
                    JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                    WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO' AND a.statusAlumno = 'ACTIVO'
                """, (clase['id_grupo'],))
                alumnos = cursor.fetchall()

                if not alumnos:
                    continue

                alumnos_ids = [al['idAlumno'] for al in alumnos]

                placeholders = ', '.join(['%s'] * len(alumnos_ids))
                query_calif = f"""
                    SELECT COUNT(*) as count FROM tb_calificaciones
                    WHERE idMateria = %s AND idGrupo = %s
                      AND idAlumno IN ({placeholders})
                      AND calificacion IS NOT NULL
                """
                params_calif = [clase['id_materia'], clase['id_grupo']] + alumnos_ids
                cursor.execute(query_calif, params_calif)
                calificados_count_row = cursor.fetchone()
                calificados_count = calificados_count_row['count'] if calificados_count_row else 0

                total_alumnos = len(alumnos_ids)
                faltantes = total_alumnos - calificados_count

                if faltantes > 0:
                    permission_result = CalificacionesService.check_captura_permission(
                        clase['id_grupo'], clase['id_materia'], id_docente, 'DOCENTE'
                    )
                    calificaciones_pendientes.append({
                        'id_grupo': clase['id_grupo'],
                        'clave_grupo': clase['clave_grupo'],
                        'id_materia': clase['id_materia'],
                        'nombre_materia': clase['nombre_materia'],
                        'clave_materia': clase['clave_materia'],
                        'alumnos_totales': total_alumnos,
                        'alumnos_faltantes': faltantes,
                        'bloqueado': not permission_result['allowed'],
                        'motivo_bloqueo': permission_result['reason']
                    })

            return {
                'prorrogas': prorrogas,
                'por_finalizar': por_finalizar,
                'calificaciones_pendientes': calificaciones_pendientes,
                'grupos': DocentesService._resumen_grupos_docente(cursor, id_docente)
            }
        except Exception as e:
            return {'error': str(e)}
        finally:
            cursor.close()
            conexion.close()
