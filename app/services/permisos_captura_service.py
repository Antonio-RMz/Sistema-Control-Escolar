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
            cursor.execute("""
                UPDATE tb_docente_permisos_captura 
                SET fecha_limite = %s, permitir_modificar_pasados = %s, habilitado = %s, updated_at = NOW()
                WHERE id = %s
            """, (
                data.get('fecha_limite') or None,
                1 if data.get('permitir_modificar_pasados') else 0,
                1 if data.get('habilitado') else 0,
                id_permiso
            ))
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
                    'p2_habilitado': 1, 'p2_fecha_inicio': None, 'p2_fecha_fin': None,
                    'p3_habilitado': 1, 'p3_fecha_inicio': None, 'p3_fecha_fin': None,
                    'semestral_habilitado': 1, 'semestral_fecha_inicio': None, 'semestral_fecha_fin': None,
                    'extraordinario_habilitado': 1, 'extraordinario_fecha_inicio': None, 'extraordinario_fecha_fin': None
                }
            
            return {
                "success": True,
                "isBgne": isBgne,
                "levels": levels,
                "config": config
            }
        finally:
            conexion.close()

    @staticmethod
    def guardar_grupo_config(grupo_id, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT 1 FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (grupo_id,))
            exists = cursor.fetchone()
            
            params = (
                data.get('id_nivel_academico') or None,
                1 if data.get('captura_habilitada') else 0,
                1 if data.get('p1_habilitado') else 0,
                data.get('p1_fecha_inicio') or None,
                data.get('p1_fecha_fin') or None,
                1 if data.get('p2_habilitado') else 0,
                data.get('p2_fecha_inicio') or None,
                data.get('p2_fecha_fin') or None,
                1 if data.get('p3_habilitado') else 0,
                data.get('p3_fecha_inicio') or None,
                data.get('p3_fecha_fin') or None,
                1 if data.get('semestral_habilitado') else 0,
                data.get('semestral_fecha_inicio') or None,
                data.get('semestral_fecha_fin') or None,
                1 if data.get('extraordinario_habilitado') else 0,
                data.get('extraordinario_fecha_inicio') or None,
                data.get('extraordinario_fecha_fin') or None,
                grupo_id
            )
            
            if exists:
                cursor.execute("""
                    UPDATE tb_grupo_periodos_captura SET
                        id_nivel_academico = %s,
                        captura_habilitada = %s,
                        p1_habilitado = %s, p1_fecha_inicio = %s, p1_fecha_fin = %s,
                        p2_habilitado = %s, p2_fecha_inicio = %s, p2_fecha_fin = %s,
                        p3_habilitado = %s, p3_fecha_inicio = %s, p3_fecha_fin = %s,
                        semestral_habilitado = %s, semestral_fecha_inicio = %s, semestral_fecha_fin = %s,
                        extraordinario_habilitado = %s, extraordinario_fecha_inicio = %s, extraordinario_fecha_fin = %s,
                        updated_at = NOW()
                    WHERE id_grupo = %s
                """, params)
            else:
                cursor.execute("""
                    INSERT INTO tb_grupo_periodos_captura (
                        id_nivel_academico, captura_habilitada,
                        p1_habilitado, p1_fecha_inicio, p1_fecha_fin,
                        p2_habilitado, p2_fecha_inicio, p2_fecha_fin,
                        p3_habilitado, p3_fecha_inicio, p3_fecha_fin,
                        semestral_habilitado, semestral_fecha_inicio, semestral_fecha_fin,
                        extraordinario_habilitado, extraordinario_fecha_inicio, extraordinario_fecha_fin,
                        id_grupo, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, params)
                
            conexion.commit()
            return {"success": True, "message": "Configuración de captura para el grupo guardada correctamente."}
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
