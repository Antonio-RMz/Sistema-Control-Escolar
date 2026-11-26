from app.config.conexion import get_connection
from datetime import date, datetime
import pymysql

class PermisosCapturaService:

    @staticmethod
    def obtener_lista_permisos():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT 
                    p.*,
                    CONCAT(d.nombreDocente, ' ', COALESCE(d.apPaternoDocente, ''), ' ', COALESCE(d.apMaternoDocente, '')) as nombre_docente,
                    g.clave as clave_grupo,
                    g.id_centroTrabajo as id_cct_grupo,
                    m.nombreMateria as nombre_materia,
                    m.clave as clave_materia
                FROM tb_docente_permisos_captura p
                LEFT JOIN tb_docentes d ON p.id_docente = d.idDocente
                LEFT JOIN tb_grupos g ON p.id_grupo = g.id
                LEFT JOIN tb_materias m ON p.id_materia = m.id
                ORDER BY p.id DESC
            """)
            permisos = cursor.fetchall()
            for p in permisos:
                for k, v in p.items():
                    if isinstance(v, (date, datetime)):
                        p[k] = str(v)
            return permisos
        finally:
            conexion.close()

    @staticmethod
    def obtener_docentes_activos():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT 
                    idDocente as id, 
                    CONCAT(nombreDocente, ' ', COALESCE(apPaternoDocente, ''), ' ', COALESCE(apMaternoDocente, '')) as nombre
                FROM tb_docentes
                WHERE statusDocente = 'ACTIVO'
                ORDER BY nombreDocente
            """)
            return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def obtener_grupos_activos():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, clave
                FROM tb_grupos
                WHERE statusGrupo = 'ACTIVO'
                ORDER BY clave
            """)
            return cursor.fetchall()
        finally:
            conexion.close()

    PERIODOS_PRORROGA = ('p1', 'p2', 'p3', 'semestral', 'extraordinario')
    _columna_periodo = None

    @staticmethod
    def _columna_periodo_disponible(cursor):
        """True si tb_docente_permisos_captura ya tiene la columna periodo (scripts/2026-11-26_prorroga_por_periodo.sql)."""
        if not PermisosCapturaService._columna_periodo:
            cursor.execute("SHOW COLUMNS FROM tb_docente_permisos_captura LIKE 'periodo'")
            PermisosCapturaService._columna_periodo = cursor.fetchone() is not None
        return PermisosCapturaService._columna_periodo

    @staticmethod
    def _periodo_prorroga(cursor, id_grupo, data):
        """Valida el periodo de la prórroga. En BTI es obligatorio. Devuelve (periodo, error)."""
        periodo = (data.get('periodo') or '').strip() or None
        if periodo and periodo not in PermisosCapturaService.PERIODOS_PRORROGA:
            return None, "Periodo de prórroga no válido."
        cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
        es_bti = int((cursor.fetchone() or {}).get('id_centroTrabajo') or 0) == 2
        if not es_bti:
            return None, None   # BGNE: la prórroga aplica a la calificación final
        if not PermisosCapturaService._columna_periodo_disponible(cursor):
            return None, ("Falta preparar la base de datos para la prórroga por periodo "
                          "(scripts/2026-11-26_prorroga_por_periodo.sql).")
        if not periodo:
            return None, "Indica a qué periodo se extiende la prórroga (parcial, semestral o extraordinario)."
        return periodo, None

    @staticmethod
    def guardar_permiso(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT 1 FROM tb_docente_permisos_captura
                WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
            """, (data.get('id_docente'), data.get('id_grupo'), data.get('id_materia')))
            if cursor.fetchone():
                return {"success": False, "message": "Ya existe un permiso registrado para este docente en esta asignatura y grupo."}

            periodo, error = PermisosCapturaService._periodo_prorroga(cursor, data.get('id_grupo'), data)
            if error:
                return {"success": False, "message": error}

            cursor.execute("""
                INSERT INTO tb_docente_permisos_captura (
                    id_docente, id_grupo, id_materia, fecha_limite, permitir_modificar_pasados, habilitado, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                data.get('id_docente'),
                data.get('id_grupo'),
                data.get('id_materia'),
                data.get('fecha_limite') or None,
                1 if data.get('permitir_modificar_pasados') else 0,
                1 if data.get('habilitado', True) else 0
            ))
            if periodo:
                cursor.execute("UPDATE tb_docente_permisos_captura SET periodo = %s WHERE id = %s",
                               (periodo, cursor.lastrowid))
            conexion.commit()
            return {"success": True, "message": "Permiso asignado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"success": False, "message": f"Error al guardar permiso: {str(e)}"}
        finally:
            conexion.close()

    @staticmethod
    def actualizar_permiso(id_permiso, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id_grupo FROM tb_docente_permisos_captura WHERE id = %s", (id_permiso,))
            actual = cursor.fetchone()
            if not actual:
                return {"success": False, "message": "La prórroga no existe."}
            periodo, error = PermisosCapturaService._periodo_prorroga(cursor, actual['id_grupo'], data)
            if error:
                return {"success": False, "message": error}

            cursor.execute("""
                UPDATE tb_docente_permisos_captura
                SET fecha_limite = %s, permitir_modificar_pasados = %s, habilitado = %s, finalizado = 0, updated_at = NOW()
                WHERE id = %s
            """, (
                data.get('fecha_limite') or None,
                1 if data.get('permitir_modificar_pasados') else 0,
                1 if data.get('habilitado') else 0,
                id_permiso
            ))
            if periodo:
                cursor.execute("UPDATE tb_docente_permisos_captura SET periodo = %s WHERE id = %s", (periodo, id_permiso))
            conexion.commit()
            return {"success": True, "message": "Permiso actualizado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"success": False, "message": f"Error al actualizar permiso: {str(e)}"}
        finally:
            conexion.close()

    @staticmethod
    def eliminar_permiso(id_permiso):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM tb_docente_permisos_captura WHERE id = %s", (id_permiso,))
            conexion.commit()
            return {"success": True, "message": "Permiso eliminado correctamente."}
        except Exception as e:
            conexion.rollback()
            return {"success": False, "message": f"Error al eliminar permiso: {str(e)}"}
        finally:
            conexion.close()

    @staticmethod
    def obtener_ccts():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, clave, nombre FROM tb_centrotrabajo")
            return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def obtener_grupos_por_cct(cct_id):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, clave
                FROM tb_grupos
                WHERE id_centroTrabajo = %s AND statusGrupo = 'ACTIVO'
                ORDER BY clave ASC
            """, (cct_id,))
            return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def obtener_grupo_config(grupo_id):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, id_tipoPeriodo, id_nivel_academico, id_centroTrabajo FROM tb_grupos WHERE id = %s", (grupo_id,))
            group = cursor.fetchone()
            if not group:
                return {"success": False, "message": "Grupo no encontrado."}
            
            cursor.execute("SELECT * FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (grupo_id,))
            config = cursor.fetchone()
            
            cursor.execute("""
                SELECT id, nombre, numero
                FROM tb_niveles_academicos
                WHERE id_tipoPeriodo = %s AND activo = 1
                ORDER BY numero ASC
            """, (group.get('id_tipoPeriodo'),))
            levels = cursor.fetchall()
            
            isBgne = int(group.get('id_centroTrabajo') or 0) == 3
            
            if config:
                for k, v in config.items():
                    if isinstance(v, (date, datetime)):
                        config[k] = str(v)
            
            for lvl in levels:
                for k, v in lvl.items():
                    if isinstance(v, (date, datetime)):
                        lvl[k] = str(v)

            if not config:
                config = {
                    'id_grupo': int(grupo_id),
                    'id_nivel_academico': group.get('id_nivel_academico'),
                    'captura_habilitada': 1,
                    'p1_habilitado': 1, 'p1_fecha_inicio': None, 'p1_fecha_fin': None,
                    'p2_habilitado': 0, 'p2_fecha_inicio': None, 'p2_fecha_fin': None,
                    'p3_habilitado': 0, 'p3_fecha_inicio': None, 'p3_fecha_fin': None,
                    'semestral_habilitado': 0, 'semestral_fecha_inicio': None, 'semestral_fecha_fin': None,
                    'extraordinario_habilitado': 0, 'extraordinario_fecha_inicio': None, 'extraordinario_fecha_fin': None
                }
            
            return {
                "success": True,
                "isBgne": isBgne,
                "levels": levels,
                "config": config
            }
        finally:
            conexion.close()

    # Periodos de tb_grupo_periodos_captura. Cada uno tiene <p>_habilitado, <p>_fecha_inicio y <p>_fecha_fin.
    _PERIODOS_GRUPO_CONFIG = ('p1', 'p2', 'p3', 'semestral', 'extraordinario')

    @staticmethod
    def _campos_grupo_config(data):
        """Columnas a guardar, solo las que vienen en la petición.

        Horarios > Fechas de Periodos de Evaluación manda solo fechas; Permisos de Captura
        manda también los *_habilitado. Así guardar fechas no reabre una captura cerrada.
        """
        campos = {}
        if 'captura_habilitada' in data:
            campos['captura_habilitada'] = 1 if data.get('captura_habilitada') else 0
        for p in PermisosCapturaService._PERIODOS_GRUPO_CONFIG:
            if f'{p}_habilitado' in data:
                campos[f'{p}_habilitado'] = 1 if data.get(f'{p}_habilitado') else 0
            for sufijo in ('fecha_inicio', 'fecha_fin'):
                k = f'{p}_{sufijo}'
                if k in data:
                    campos[k] = data.get(k) or None
        return campos

    @staticmethod
    def _upsert_grupo_config(cursor, id_grupo, nivel_id, campos):
        """Actualiza (o crea) la config del grupo. Las columnas omitidas conservan su valor
        (o el default de la tabla al insertar). Los nombres de columna vienen de una lista fija."""
        valores = {'id_nivel_academico': nivel_id, **campos}
        cols = list(valores)
        cursor.execute("SELECT 1 FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
        if cursor.fetchone():
            sets = ', '.join(f'{c} = %s' for c in cols)
            cursor.execute(
                f"UPDATE tb_grupo_periodos_captura SET {sets}, updated_at = NOW() WHERE id_grupo = %s",
                (*valores.values(), id_grupo)
            )
        else:
            marcas = ', '.join(['%s'] * len(cols))
            cursor.execute(
                f"INSERT INTO tb_grupo_periodos_captura ({', '.join(cols)}, id_grupo, created_at, updated_at) "
                f"VALUES ({marcas}, %s, NOW(), NOW())",
                (*valores.values(), id_grupo)
            )

    @staticmethod
    def guardar_grupo_config(grupo_id, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, id_tipoPeriodo, id_nivel_academico, id_centroTrabajo FROM tb_grupos WHERE id = %s", (grupo_id,))
            group = cursor.fetchone()
            if not group:
                return {"success": False, "message": "Grupo no encontrado."}

            data = data or {}
            nivel_id = data.get('id_nivel_academico') or group.get('id_nivel_academico')
            campos = PermisosCapturaService._campos_grupo_config(data)

            PermisosCapturaService._upsert_grupo_config(cursor, grupo_id, nivel_id, campos)

            replicados = 0
            if data.get('replicar_mismo_semestre'):
                cct = group.get('id_centroTrabajo')
                if cct and nivel_id:
                    cursor.execute("""
                        SELECT id FROM tb_grupos 
                        WHERE id_centroTrabajo = %s 
                          AND id_nivel_academico = %s 
                          AND statusGrupo = 'ACTIVO' 
                          AND id != %s
                    """, (cct, nivel_id, grupo_id))
                    for otro in cursor.fetchall():
                        PermisosCapturaService._upsert_grupo_config(cursor, otro['id'], nivel_id, campos)
                        replicados += 1

            conexion.commit()
            msg = "Configuración de fechas de evaluación guardada correctamente."
            if replicados > 0:
                msg += f" (Replicada a {replicados} grupo(s) del mismo nivel/CCT)."
            return {"success": True, "message": msg, "replicados": replicados}
        except Exception as e:
            conexion.rollback()
            return {"success": False, "message": f"Error al guardar configuración: {str(e)}"}
        finally:
            conexion.close()

    @staticmethod
    def obtener_matriz_avance():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            hoy_str = date.today().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT DISTINCT
                    h.id_docente,
                    h.id_grupo,
                    h.id_materia,
                    CONCAT(d.nombreDocente, ' ', COALESCE(d.apPaternoDocente, ''), ' ', COALESCE(d.apMaternoDocente, '')) as nombre_docente,
                    g.clave as clave_grupo,
                    g.fechaFin as fecha_fin_grupo,
                    g.statusGrupo as status_grupo,
                    g.id_nivel_academico as id_nivel_grupo,
                    m.nombreMateria as nombre_materia,
                    m.clave as clave_materia,
                    m.id_nivel_academico as id_nivel_materia
                FROM tb_horarios h
                JOIN tb_docentes d ON h.id_docente = d.idDocente
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE m.id_nivel_academico IS NULL OR m.id_nivel_academico = g.id_nivel_academico
                ORDER BY g.clave ASC, nombre_docente ASC
            """)
            horarios = cursor.fetchall()
            
            matriz = []
            for h in horarios:
                id_grupo = h['id_grupo']
                id_materia = h['id_materia']
                id_docente = h['id_docente']
                
                cursor.execute("""
                    SELECT a.idAlumno
                    FROM tb_alumnogrupo ag
                    JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                    WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO' AND a.statusAlumno = 'ACTIVO'
                """, (id_grupo,))
                alumnos = cursor.fetchall()
                total_alumnos = len(alumnos)
                
                graded_count = 0
                if total_alumnos > 0:
                    alumnos_ids = [a['idAlumno'] for a in alumnos]
                    placeholders = ', '.join(['%s'] * len(alumnos_ids))
                    query = f"""
                        SELECT COUNT(*) as cnt 
                        FROM tb_calificaciones 
                        WHERE idMateria = %s AND idGrupo = %s AND idAlumno IN ({placeholders}) AND calificacion IS NOT NULL
                    """
                    cursor.execute(query, [id_materia, id_grupo] + alumnos_ids)
                    res_cnt = cursor.fetchone()
                    graded_count = res_cnt['cnt'] if res_cnt else 0
                
                cursor.execute("""
                    SELECT * FROM tb_docente_permisos_captura
                    WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                    LIMIT 1
                """, (id_docente, id_grupo, id_materia))
                permiso = cursor.fetchone()
                
                if permiso:
                    for k, v in permiso.items():
                        if isinstance(v, (date, datetime)):
                            permiso[k] = str(v)
                
                estado = 'pendiente'
                motivo = 'Captura en tiempo ordinario'
                fecha_limite = h['fecha_fin_grupo']
                if isinstance(fecha_limite, (date, datetime)):
                    fecha_limite = str(fecha_limite)
                
                if total_alumnos == 0:
                    estado = 'sin_alumnos'
                    motivo = 'Sin alumnos inscritos'
                elif graded_count == total_alumnos:
                    estado = 'completo'
                    motivo = 'Captura completa'
                else:
                    if permiso and not permiso.get('habilitado'):
                        estado = 'deshabilitado'
                        motivo = 'Bloqueado por administrador'
                    else:
                        es_periodo_pasado = False
                        id_nivel_grupo = h['id_nivel_grupo']
                        id_nivel_materia = h['id_nivel_materia']
                        
                        if id_nivel_grupo and id_nivel_materia:
                            cursor.execute("SELECT numero FROM tb_niveles_academicos WHERE id = %s", (id_nivel_grupo,))
                            nivel_grupo = cursor.fetchone()
                            cursor.execute("SELECT numero FROM tb_niveles_academicos WHERE id = %s", (id_nivel_materia,))
                            nivel_materia = cursor.fetchone()
                            if nivel_grupo and nivel_materia and nivel_materia['numero'] < nivel_grupo['numero']:
                                es_periodo_pasado = True
                        
                        if h['status_grupo'] and h['status_grupo'].upper() != 'ACTIVO':
                            es_periodo_pasado = True
                            
                        if es_periodo_pasado:
                            if permiso and permiso.get('permitir_modificar_pasados'):
                                if permiso.get('fecha_limite'):
                                    fecha_limite = str(permiso.get('fecha_limite'))
                                    if hoy_str > fecha_limite:
                                        estado = 'expirado'
                                        motivo = 'Prórroga histórica vencida'
                                    else:
                                        estado = 'prorroga'
                                        motivo = 'Prórroga histórica activa'
                                else:
                                    estado = 'prorroga'
                                    motivo = 'Autorización histórica activa'
                            else:
                                estado = 'bloqueado_pasado'
                                motivo = 'Periodo pasado - Requiere permiso'
                        else:
                            if permiso and permiso.get('fecha_limite'):
                                fecha_limite = str(permiso.get('fecha_limite'))
                                if hoy_str > fecha_limite:
                                    estado = 'expirado'
                                    motivo = 'Prórroga vencida'
                                else:
                                    estado = 'prorroga'
                                    motivo = 'Prórroga activa'
                            else:
                                if h['fecha_fin_grupo']:
                                    fecha_fin_grupo_str = str(h['fecha_fin_grupo'])
                                    if hoy_str > fecha_fin_grupo_str:
                                        estado = 'expirado'
                                        motivo = 'Plazo vencido'
                                    else:
                                        estado = 'pendiente'
                                        motivo = 'En tiempo ordinario'
                                else:
                                    estado = 'pendiente'
                                    motivo = 'En tiempo ordinario'
                                    
                matriz.append({
                    'id_docente': id_docente,
                    'nombre_docente': h['nombre_docente'],
                    'id_grupo': id_grupo,
                    'clave_grupo': h['clave_grupo'],
                    'id_materia': id_materia,
                    'nombre_materia': h['nombre_materia'],
                    'clave_materia': h['clave_materia'],
                    'alumnos_totales': total_alumnos,
                    'alumnos_calificados': graded_count,
                    'estado': estado,
                    'motivo': motivo,
                    'fecha_limite': fecha_limite,
                    'permiso': permiso
                })
                
            return matriz
        finally:
            conexion.close()
