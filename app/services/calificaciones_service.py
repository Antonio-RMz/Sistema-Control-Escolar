from app.config.conexion import get_connection
from datetime import date, datetime
import pymysql
import unicodedata
import re

def normalize_subject_name(name):
    if not name:
        return ""
    name = name.upper().strip()
    
    # Handle accents
    name = "".join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Standardize abbreviations and punctuation
    name = name.replace("MET. DE LA INVESTIGACION II", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("MET. DE LA INVESTIGACIÓN II", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("MET. DE LA INVESTIGACION I", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACIÓN I", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACION", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACIÓN", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("ECOLOGIA Y MED. AMBIENTE", "ECOLOGIA Y MEDIO AMBIENTE")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MEXICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MÉXICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    name = name.replace("INGLES 1", "INGLES I")
    name = name.replace("INGLES 2", "INGLES II")
    name = name.replace("INGLES 3", "INGLES III")
    name = name.replace("INGLES 4", "INGLES IV")
    name = name.replace("INGLES 5", "INGLES V")
    name = name.replace("INGLES 6", "INGLES VI")
    
    # Force numeric replacements for user prompt matches
    name = name.replace("MATEMATICAS 4", "MATEMATICAS IV")
    name = name.replace("MATEMÁTICAS 4", "MATEMATICAS IV")
    name = name.replace("MATEMATICAS 1", "MATEMATICAS I")
    name = name.replace("MATEMATICAS 2", "MATEMATICAS II")
    name = name.replace("MATEMATICAS 3", "MATEMATICAS III")
    
    name = name.replace("METODO DE LA INVESTIGACION 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODO DE LA INVESTIGACIÓN 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODOLOGIA DE LA INVESTIGACION 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODOLOGÍA DE LA INVESTIGACIÓN 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODO DE LA INVESTIGACION 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODO DE LA INVESTIGACIÓN 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODOLOGIA DE LA INVESTIGACION 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODOLOGÍA DE LA INVESTIGACIÓN 2", "METODOLOGIA DE LA INVESTIGACION II")
    
    name = name.replace("BIOLOGIA 1", "BIOLOGIA I")
    name = name.replace("BIOLOGÍA 1", "BIOLOGIA I")
    name = name.replace("BIOLOGIA 2", "BIOLOGIA II")
    name = name.replace("BIOLOGÍA 2", "BIOLOGIA II")
    
    name = name.replace("FISICA 1", "FISICA I")
    name = name.replace("FÍSICA 1", "FISICA I")
    name = name.replace("FISICA 2", "FISICA II")
    name = name.replace("FÍSICA 2", "FISICA II")
    
    name = name.replace("LITERATURA 1", "LITERATURA I")
    name = name.replace("LITERATURA 2", "LITERATURA II")
    
    name = name.replace("CONTABILIDAD 1", "CONTABILIDAD I")
    name = name.replace("CONTABILIDAD 2", "CONTABILIDAD II")
    
    name = name.replace("TEMAS SELECTOS DE BIOLOGIA 1", "TEMAS SELECTOS DE BIOLOGIA I")
    name = name.replace("TEMAS SELECTOS DE BIOLOGÍA 1", "TEMAS SELECTOS DE BIOLOGIA I")
    name = name.replace("TEMAS SELECTOS DE BIOLOGIA 2", "TEMAS SELECTOS DE BIOLOGIA II")
    name = name.replace("TEMAS SELECTOS DE BIOLOGÍA 2", "TEMAS SELECTOS DE BIOLOGIA II")
    
    name = name.replace("INFORMATICA 1", "INFORMATICA I")
    name = name.replace("INFORMATICA 2", "INFORMATICA II")
    name = name.replace("INFORMATICA 3", "INFORMATICA III")
    name = name.replace("INFORMATICA 4", "INFORMATICA IV")
    name = name.replace("INFORMÁTICA 1", "INFORMATICA I")
    name = name.replace("INFORMÁTICA 2", "INFORMATICA II")
    name = name.replace("INFORMÁTICA 3", "INFORMATICA III")
    name = name.replace("INFORMÁTICA 4", "INFORMATICA IV")
    
    name = re.sub(r'[^A-Z0-9]', ' ', name)
    name = " ".join(name.split())
    return name

BGNE_CANONICAL_LEVELS = {
    "MATEMATICAS I": 1, "QUIMICA I": 1, "GEOGRAFIA": 1, "INTRODUCCION C. SOCIALES I": 1, "INFORMATICA I": 1, "LECTURA Y REDACCION I": 1, "INGLES I": 1,
    "MATEMATICAS II": 2, "QUIMICA II": 2, "BIOLOGIA I": 2, "HISTORIA DE MEXICO I": 2, "INFORMATICA II": 2, "LECTURA Y REDACCION II": 2, "INGLES II": 2,
    "MATEMATICAS III": 3, "FISICA I": 3, "METODOLOGIA DE LA INVESTIGACION I": 3, "HISTORIA DE MEXICO II": 3, "BIOLOGIA II": 3, "LITERATURA I": 3, "INGLES III": 3,
    "MATEMATICAS IV": 4, "FISICA II": 4, "ECOLOGIA Y MEDIO AMBIENTE": 4, "ESTRUCTURA SOCIOECONOMICA DE MEXICO": 4, "METODOLOGIA DE LA INVESTIGACION II": 4, "LITERATURA II": 4, "INGLES IV": 4,
    "INFORMATICA III": 5, "INGLES V": 5, "CALCULO DIFERENCIAL": 5, "CONTABILIDAD I": 5, "INDIVIDUO Y SOCIEDAD": 5, "TEMAS SELECTOS DE BIOLOGIA I": 5,
    "FILOSOFIA": 6, "INGLES VI": 6, "CALCULO INTEGRAL": 6, "TEMAS SELECTOS DE BIOLOGIA II": 6, "INFORMATICA IV": 6, "CONTABILIDAD II": 6,
}

BGNE_NORMALIZED_CANONICAL = {normalize_subject_name(k): v for k, v in BGNE_CANONICAL_LEVELS.items()}

class CalificacionesService:

    @staticmethod
    def get_kardex_alumno(id_alumno):
        """
        Obtiene el Kárdex completo del alumno organizado por Periodos/Niveles Académicos,
        calculando los promedios por periodo y el promedio global.
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Obtener datos generales del alumno y su CCT
            cursor.execute("""
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.id_nivel_ingreso,
                    nei.numero AS numeroNivelIngreso,
                    COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3) AS id_centroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    ct.clave AS claveCentroTrabajo,
                    g.nombreGeneracion,
                    gr.clave AS claveGrupo
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON ct.id = COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3)
                LEFT JOIN tb_niveles_academicos nei ON a.id_nivel_ingreso = nei.id
                WHERE a.idAlumno = %s
            """, (id_alumno,))
            alumno = cursor.fetchone()
            if not alumno:
                return {"error": "Alumno no encontrado"}

            id_cct = alumno["id_centroTrabajo"]

            # 2. Obtener los niveles académicos correspondientes a este CCT (ej. 1º a 6º Trimestre o Semestre)
            cursor.execute("""
                SELECT 
                    n.id AS idNivel,
                    n.nombre AS nombreNivel,
                    n.numero AS numeroNivel,
                    n.tipo AS tipoPeriodo
                FROM tb_niveles_academicos n
                JOIN tb_tipoperiodo tp ON n.id_tipoPeriodo = tp.id
                JOIN tb_centrotrabajo ct ON ct.idTipoPeriodo = tp.id
                WHERE ct.id = %s AND n.activo = 1
                ORDER BY n.numero ASC
            """, (id_cct,))
            niveles = cursor.fetchall()
            if not niveles:
                # Fallback: consultar todos los niveles del tipo de periodo de BGNE o BTI
                cursor.execute("SELECT id AS idNivel, nombre AS nombreNivel, numero AS numeroNivel, tipo AS tipoPeriodo FROM tb_niveles_academicos ORDER BY id_tipoPeriodo ASC, numero ASC")
                niveles = cursor.fetchall()

            # 3. Obtener materias y calificaciones
            is_bgne = (id_cct == 3)
            
            if is_bgne:
                # Obtener todas las materias asignadas a este CCT (BGNe) o globales
                cursor.execute("""
                    SELECT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        m.orden
                    FROM tb_materias m
                    WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
                """, (id_cct,))
                todas_materias = cursor.fetchall()
                
                # Obtener calificaciones del alumno
                cursor.execute("""
                    SELECT 
                        c.id AS idCalificacion,
                        c.idMateria,
                        c.calificacion,
                        c.tipoAcreditacion,
                        c.observaciones,
                        c.fechaEvaluacion,
                        c.idGrupo,
                        c.parcial1,
                        c.parcial2,
                        c.parcial3,
                        c.semestral,
                        c.extraordinario,
                        c.asistencias,
                        c.total_asistencias,
                        m.nombreMateria,
                        m.id_nivel_academico AS level_materia
                    FROM tb_calificaciones c
                    JOIN tb_materias m ON c.idMateria = m.id
                    WHERE c.idAlumno = %s
                """, (id_alumno,))
                calificaciones = cursor.fetchall()
                
                # Agrupar calificaciones por nombre normalizado
                califs_mapped = {}
                for calif in calificaciones:
                    norm_name = normalize_subject_name(calif["nombreMateria"])
                    if norm_name not in califs_mapped:
                        califs_mapped[norm_name] = calif
                    else:
                        existing = califs_mapped[norm_name]
                        e_val = existing.get("calificacion")
                        n_val = calif.get("calificacion")
                        if n_val is not None:
                            if e_val is None or n_val > e_val:
                                califs_mapped[norm_name] = calif
                                
                # Filtrar materias a mostrar en base a canonical levels
                materias_filtradas = []
                for mat in todas_materias:
                    m_id = mat["idMateria"]
                    m_name = mat["nombreMateria"]
                    m_level = mat["id_nivel_academico"]
                    
                    norm_name = normalize_subject_name(m_name)
                    if norm_name in BGNE_NORMALIZED_CANONICAL:
                        canonical_level = BGNE_NORMALIZED_CANONICAL[norm_name]
                        if m_level == canonical_level:
                            mat["id_nivel_academico"] = canonical_level
                            materias_filtradas.append(mat)
                        else:
                            # Registro duplicado de materia en otro nivel - omitir del kárdex
                            continue
                    else:
                        # Materia no canónica - conservar en su nivel actual
                        materias_filtradas.append(mat)
                        
                # Combinar materias y calificaciones
                materias_califs = []
                for mat in materias_filtradas:
                    m_id = mat["idMateria"]
                    m_name = mat["nombreMateria"]
                    norm_name = normalize_subject_name(m_name)
                    calif = califs_mapped.get(norm_name)
                    
                    row = {
                        "idMateria": m_id,
                        "nombreMateria": m_name,
                        "claveMateria": mat["claveMateria"],
                        "id_nivel_academico": mat["id_nivel_academico"],
                        "orden": mat.get("orden"),
                        "idCalificacion": calif["idCalificacion"] if calif else None,
                        "calificacion": float(calif["calificacion"]) if calif and calif["calificacion"] is not None else None,
                        "tipoAcreditacion": calif["tipoAcreditacion"] if calif else None,
                        "observaciones": calif["observaciones"] if calif else None,
                        "fechaEvaluacion": calif["fechaEvaluacion"] if calif else None,
                        "idGrupo": calif["idGrupo"] if calif else None,
                        "parcial1": calif["parcial1"] if calif else None,
                        "parcial2": calif["parcial2"] if calif else None,
                        "parcial3": calif["parcial3"] if calif else None,
                        "semestral": calif["semestral"] if calif else None,
                        "extraordinario": calif["extraordinario"] if calif else None,
                        "asistencias": calif["asistencias"] if calif else None,
                        "total_asistencias": calif["total_asistencias"] if calif else None,
                    }
                    materias_califs.append(row)
                    
                # Ordenar por nivel, orden y materia id
                materias_califs.sort(key=lambda x: (x["id_nivel_academico"] or 99, x.get("orden") if x.get("orden") is not None else 9999, x["idMateria"]))
                
            else:
                # Comportamiento original para otros planes (BTI, etc.)
                cursor.execute("""
                    SELECT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        c.id AS idCalificacion,
                        c.calificacion,
                        c.tipoAcreditacion,
                        c.observaciones,
                        c.fechaEvaluacion,
                        c.idGrupo,
                        c.parcial1,
                        c.parcial2,
                        c.parcial3,
                        c.semestral,
                        c.extraordinario,
                        c.asistencias,
                        c.total_asistencias
                    FROM tb_materias m
                    LEFT JOIN tb_calificaciones c ON c.idMateria = m.id AND c.idAlumno = %s
                    WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
                    ORDER BY m.id_nivel_academico ASC, COALESCE(m.orden, m.id) ASC
                """, (id_alumno, id_cct))
                materias_califs = cursor.fetchall()

            # 4. Agrupar materias y calificaciones por Nivel Académico
            kardex_periodos = []
            suma_calif_global = 0.0
            total_materias_evaluadas = 0

            for nivel in niveles:
                id_nivel = nivel["idNivel"]
                mats_nivel = [m for m in materias_califs if m.get("id_nivel_academico") == id_nivel]
                
                suma_periodo = 0.0
                evaluadas_periodo = 0

                lista_materias_periodo = []
                for mat in mats_nivel:
                    calif_val = mat.get("calificacion")
                    tiene_calif = calif_val is not None
                    
                    is_equiv = False
                    if alumno.get("equivalencia") == "SI" and alumno.get("numeroNivelIngreso") is not None:
                        if int(alumno["numeroNivelIngreso"]) > int(nivel["numeroNivel"]):
                            is_equiv = True
                    
                    if tiene_calif:
                        c_num = float(calif_val)
                        suma_periodo += c_num
                        evaluadas_periodo += 1
                        suma_calif_global += c_num
                        total_materias_evaluadas += 1

                    lista_materias_periodo.append({
                        "idMateria": mat["idMateria"],
                        "nombreMateria": mat["nombreMateria"],
                        "claveMateria": mat["claveMateria"],
                        "idCalificacion": mat["idCalificacion"],
                        "calificacion": float(calif_val) if tiene_calif else None,
                        "es_equivalencia": is_equiv,
                        "tipoAcreditacion": mat.get("tipoAcreditacion") or ("EQUIVALENCIA" if is_equiv else "ORDINARIO"),
                        "observaciones": mat.get("observaciones"),
                        "fechaEvaluacion": str(mat["fechaEvaluacion"]) if mat.get("fechaEvaluacion") else None,
                        "aprobada": float(calif_val) >= 6.0 if tiene_calif else False,
                        "parcial1": float(mat["parcial1"]) if mat.get("parcial1") is not None else None,
                        "parcial2": float(mat["parcial2"]) if mat.get("parcial2") is not None else None,
                        "parcial3": float(mat["parcial3"]) if mat.get("parcial3") is not None else None,
                        "semestral": float(mat["semestral"]) if mat.get("semestral") is not None else None,
                        "extraordinario": float(mat["extraordinario"]) if mat.get("extraordinario") is not None else None,
                        "asistencias": int(mat["asistencias"]) if mat.get("asistencias") is not None else None,
                        "total_asistencias": int(mat["total_asistencias"]) if mat.get("total_asistencias") is not None else None,
                    })

                promedio_periodo = round(suma_periodo / evaluadas_periodo, 1) if evaluadas_periodo > 0 else None

                kardex_periodos.append({
                    "idNivel": id_nivel,
                    "nombrePeriodo": nivel["nombreNivel"],
                    "numeroPeriodo": nivel["numeroNivel"],
                    "tipoPeriodo": nivel["tipoPeriodo"],
                    "materias": lista_materias_periodo,
                    "promedio": promedio_periodo,
                    "totalMaterias": len(lista_materias_periodo),
                    "totalAcreditadas": sum(1 for m in lista_materias_periodo if m["aprobada"])
                })

            promedio_general = round(suma_calif_global / total_materias_evaluadas, 1) if total_materias_evaluadas > 0 else None

            return {
                "alumno": alumno,
                "periodos": kardex_periodos,
                "promedioGeneral": promedio_general,
                "totalMateriasEvaluadas": total_materias_evaluadas
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_calificaciones_alumno(id_alumno, calificaciones, create_by="SISTEMA"):
        """
        Guarda o actualiza una lista de calificaciones para un alumno.
        calificaciones: [ { "idMateria": 8, "id_nivel_academico": 1, "calificacion": 8.5, "tipoAcreditacion": "ORDINARIO", "observaciones": "..." } ]
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            for item in calificaciones:
                id_materia = item.get("idMateria")
                calificacion = item.get("calificacion")
                id_nivel = item.get("id_nivel_academico")
                tipo_acred = item.get("tipoAcreditacion") or "ORDINARIO"
                observaciones = item.get("observaciones")
                id_grupo = item.get("idGrupo") or None

                if not id_materia:
                    continue

                if calificacion is None:
                    # Si la calificación se envía vacía o se revierte a equivalencia, eliminar la calificación si existe
                    cursor.execute("""
                        DELETE FROM tb_calificaciones 
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                    """, (id_alumno, id_materia, tipo_acred))
                    continue

                # Verificar si ya existe calificación para este alumno, materia y tipo de acreditación
                cursor.execute("""
                    SELECT id FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                """, (id_alumno, id_materia, tipo_acred))
                existente = cursor.fetchone()

                parcial1 = item.get("parcial1")
                parcial2 = item.get("parcial2")
                parcial3 = item.get("parcial3")
                semestral = item.get("semestral")
                extraordinario = item.get("extraordinario")
                asistencias = item.get("asistencias")
                total_asistencias = item.get("total_asistencias")

                p1_val = float(parcial1) if (parcial1 is not None and parcial1 != "") else None
                p2_val = float(parcial2) if (parcial2 is not None and parcial2 != "") else None
                p3_val = float(parcial3) if (parcial3 is not None and parcial3 != "") else None
                sem_val = float(semestral) if (semestral is not None and semestral != "") else None
                ext_val = float(extraordinario) if (extraordinario is not None and extraordinario != "") else None
                asist_val = int(asistencias) if (asistencias is not None and asistencias != "") else None
                tot_asist_val = int(total_asistencias) if (total_asistencias is not None and total_asistencias != "") else None

                if existente:
                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, id_nivel_academico = %s, idGrupo = %s, observaciones = %s,
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s, 
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calificacion, id_nivel, id_grupo, observaciones, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val, create_by, existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones (
                            idAlumno, idMateria, id_nivel_academico, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy,
                            parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_alumno, id_materia, id_nivel, id_grupo, calificacion, tipo_acred, observaciones, create_by, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val))

            conexion.commit()
            return {"success": True, "message": "Calificaciones guardadas exitosamente"}
        except Exception as e:
            conexion.rollback()
    def check_captura_permission(id_grupo, id_materia, id_docente, rol):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            if rol and rol.upper() == 'ADMIN':
                return {
                    'allowed': True,
                    'reason': 'Acceso administrador total.'
                }

            if not id_docente:
                return {
                    'allowed': False,
                    'reason': 'Identificación de docente no encontrada.'
                }

            hoy = date.today().strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT habilitado, fecha_limite, permitir_modificar_pasados, finalizado 
                FROM tb_docente_permisos_captura
                WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
            """, (id_docente, id_grupo, id_materia))
            permiso = cursor.fetchone()

            if permiso and (permiso.get('finalizado') == 1 or permiso.get('finalizado') is True):
                return {
                    'allowed': False,
                    'reason': 'Las calificaciones de esta asignatura ya fueron enviadas y confirmadas. Solo el administrador puede realizar cambios.'
                }

            if permiso and not permiso.get('habilitado'):
                return {
                    'allowed': False,
                    'reason': 'La captura de calificaciones ha sido deshabilitada para esta asignatura por administración.'
                }

            if not permiso:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM tb_horarios
                        WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                    ) AS exist
                """, (id_docente, id_grupo, id_materia))
                horario_exist = cursor.fetchone()
                if not horario_exist or not horario_exist.get('exist'):
                    return {
                        'allowed': False,
                        'reason': 'No tienes asignada esta asignatura en este grupo.'
                    }

            cursor.execute("SELECT statusGrupo, fechaFin, id_nivel_academico FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo = cursor.fetchone()
            
            cursor.execute("SELECT id_nivel_academico FROM tb_materias WHERE id = %s", (id_materia,))
            materia = cursor.fetchone()

            if not grupo:
                return {
                    'allowed': False,
                    'reason': 'El grupo no existe.'
                }

            if not permiso:
                cursor.execute("SELECT captura_habilitada FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
                grp_config = cursor.fetchone()
                if grp_config and not grp_config.get('captura_habilitada'):
                    return {
                        'allowed': False,
                        'reason': 'La captura de calificaciones está deshabilitada temporalmente para este grupo.'
                    }

            if grupo.get('statusGrupo') and grupo.get('statusGrupo').upper() != 'ACTIVO':
                if not permiso or not permiso.get('permitir_modificar_pasados'):
                    return {
                        'allowed': False,
                        'reason': 'El grupo se encuentra inactivo. Requiere autorización especial de administración.'
                    }

            if grupo and materia:
                g_lvl_id = grupo.get('id_nivel_academico')
                m_lvl_id = materia.get('id_nivel_academico')
                if g_lvl_id is not None and m_lvl_id is not None:
                    cursor.execute("SELECT numero, nombre FROM tb_niveles_academicos WHERE id = %s", (g_lvl_id,))
                    nivel_grupo = cursor.fetchone()
                    cursor.execute("SELECT numero, nombre FROM tb_niveles_academicos WHERE id = %s", (m_lvl_id,))
                    nivel_materia = cursor.fetchone()
                    
                    if nivel_grupo and nivel_materia:
                        if int(nivel_materia.get('numero') or 0) < int(nivel_grupo.get('numero') or 0):
                            if not permiso or not permiso.get('permitir_modificar_pasados'):
                                return {
                                    'allowed': False,
                                    'reason': f"Esta asignatura pertenece a un periodo anterior ({nivel_materia.get('nombre')}). Requiere autorización de administración para modificar calificaciones pasadas."
                                }

            if permiso and permiso.get('fecha_limite'):
                fecha_limite_str = str(permiso.get('fecha_limite'))
                if hoy > fecha_limite_str:
                    return {
                        'allowed': False,
                        'reason': f"El periodo extraordinario de captura expiró el {datetime.strptime(fecha_limite_str, '%Y-%m-%d').strftime('%d/%m/%Y')}."
                    }
            else:
                if grupo.get('fechaFin'):
                    fecha_fin_str = str(grupo.get('fechaFin'))
                    if hoy > fecha_fin_str:
                        return {
                            'allowed': False,
                            'reason': f"El periodo ordinario de captura finalizó el {datetime.strptime(fecha_fin_str, '%Y-%m-%d').strftime('%d/%m/%Y')}."
                        }

            return {
                'allowed': True,
                'reason': 'Permiso concedido.'
            }
        except Exception as e:
            return {
                'allowed': False,
                'reason': f"Error al verificar permisos: {str(e)}"
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_calificaciones_grupo_materia(id_grupo, id_materia=None, id_docente=None, rol=None):
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # 1. Información del grupo
            cursor.execute("""
                SELECT 
                    g.id,
                    g.clave,
                    g.fechaInicio,
                    g.fechaFin,
                    g.id_centroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    ct.clave AS claveCentroTrabajo,
                    g.id_nivel_academico,
                    na.nombre AS nombreNivel,
                    g.modalidadHorario,
                    g.statusGrupo,
                    tp.nombrePeriodo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                LEFT JOIN tb_niveles_academicos na ON g.id_nivel_academico = na.id
                LEFT JOIN tb_tipoperiodo tp ON g.id_tipoPeriodo = tp.id
                WHERE g.id = %s
            """, (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado"}

            # 2. Obtener materias y docentes asociados a este grupo (de tb_horarios o del CCT)
            cursor.execute("""
                SELECT DISTINCT 
                    m.id AS idMateria,
                    m.nombreMateria,
                    m.clave AS claveMateria,
                    m.id_nivel_academico,
                    na.nombre AS nombreNivel,
                    na.numero AS numeroNivel,
                    h.id_docente,
                    CONCAT(d.nombreDocente, ' ', IFNULL(d.apPaternoDocente, ''), ' ', IFNULL(d.apMaternoDocente, '')) AS nombreDocente,
                    d.nivelEstudios,
                    COALESCE(m.orden, m.id) AS ordenMateria
                FROM tb_horarios h
                JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_niveles_academicos na ON m.id_nivel_academico = na.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s
                ORDER BY ordenMateria ASC
            """, (id_grupo,))
            materias_horario = cursor.fetchall()

            # Si no hay materias en tb_horarios para este grupo, traer las materias de su CCT/Nivel
            if not materias_horario:
                cursor.execute("""
                    SELECT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        na.nombre AS nombreNivel,
                        na.numero AS numeroNivel,
                        NULL AS id_docente,
                        'Sin docente asignado' AS nombreDocente,
                        NULL AS nivelEstudios,
                        COALESCE(m.orden, m.id) AS ordenMateria
                    FROM tb_materias m
                    LEFT JOIN tb_niveles_academicos na ON m.id_nivel_academico = na.id
                    WHERE m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL
                    ORDER BY m.id_nivel_academico ASC, ordenMateria ASC
                """, (grupo.get("id_centro_trabajo") or grupo.get("id_centroTrabajo") or 3,))
                materias_horario = cursor.fetchall()

            # Filtrar materias si es rol DOCENTE
            is_docente = rol and rol.upper() == 'DOCENTE'
            group_level = grupo.get("id_nivel_academico")
            
            if is_docente and id_docente:
                filtered_materias = []
                for m in materias_horario:
                    match_docente = m.get("id_docente") is not None and int(m["id_docente"]) == int(id_docente)
                    match_level = m.get("id_nivel_academico") is None or (group_level is not None and int(m["id_nivel_academico"]) == int(group_level))
                    if match_docente and match_level:
                        filtered_materias.append(m)
                materias_horario = filtered_materias

            # Si no hay id_materia, tomar la primera
            if not id_materia and materias_horario:
                if is_docente and id_docente:
                    cursor.execute("""
                        SELECT h.id_materia FROM tb_horarios h
                        JOIN tb_materias m ON h.id_materia = m.id
                        WHERE h.id_grupo = %s AND h.id_docente = %s
                        AND (m.id_nivel_academico IS NULL OR m.id_nivel_academico = %s)
                        ORDER BY h.id_materia ASC LIMIT 1
                    """, (id_grupo, id_docente, group_level))
                    first_horario = cursor.fetchone()
                    if first_horario:
                        id_materia = first_horario["id_materia"]
                
                if not id_materia:
                    id_materia = materias_horario[0]["idMateria"]

            # Docente de la materia seleccionada
            materia_seleccionada = None
            for m in materias_horario:
                if str(m["idMateria"]) == str(id_materia):
                    materia_seleccionada = m
                    break

            # Si el rol es DOCENTE y id_materia no está en materias_horario, reajustarla
            if is_docente and id_docente and id_materia and not materia_seleccionada:
                for m in materias_horario:
                    if str(m["idMateria"]) == str(id_materia) and m.get("id_docente") is not None and int(m["id_docente"]) == int(id_docente):
                        materia_seleccionada = m
                        break

            # 3. Lista de alumnos del grupo con sus calificaciones en esta materia
            alumnos_califs = []
            if id_materia:
                # Obtener el número de nivel de la materia actual
                numero_nivel_materia = 1
                if materia_seleccionada and materia_seleccionada.get("numeroNivel") is not None:
                    numero_nivel_materia = int(materia_seleccionada["numeroNivel"])
                else:
                    cursor.execute("SELECT numero FROM tb_niveles_academicos WHERE id = (SELECT id_nivel_academico FROM tb_materias WHERE id = %s)", (id_materia,))
                    nivel_row = cursor.fetchone()
                    if nivel_row and nivel_row.get("numero") is not None:
                        numero_nivel_materia = int(nivel_row["numero"])

                cursor.execute("""
                    SELECT 
                        a.idAlumno,
                        a.numeroControl AS matricula,
                        a.nombre,
                        a.apPaterno,
                        a.apMaterno,
                        a.curp,
                        a.statusAlumno,
                        a.equivalencia,
                        a.id_nivel_ingreso,
                        nei.numero AS numeroNivelIngreso,
                        c.id AS idCalificacion,
                        c.calificacion,
                        c.tipoAcreditacion,
                        c.observaciones,
                        c.parcial1,
                        c.parcial2,
                        c.parcial3,
                        c.semestral,
                        c.extraordinario,
                        c.asistencias,
                        c.total_asistencias
                    FROM tb_alumnos a
                    LEFT JOIN tb_niveles_academicos nei ON a.id_nivel_ingreso = nei.id
                    LEFT JOIN tb_calificaciones c ON c.idAlumno = a.idAlumno AND c.idMateria = %s
                    WHERE a.idGrupo = %s
                    ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
                """, (id_materia, id_grupo))
                alumnos_califs = cursor.fetchall()

                # Determinar si cada alumno tiene estatus de equivalencia para este periodo
                for a in alumnos_califs:
                    is_equiv = False
                    if a.get("equivalencia") == "SI" and a.get("numeroNivelIngreso") is not None:
                        if int(a["numeroNivelIngreso"]) > numero_nivel_materia:
                            is_equiv = True
                    a["es_equivalencia"] = is_equiv

            # 4. Lógica de permisos de captura
            solo_lectura = False
            mensaje_restriccion = ""
            
            permiso = None
            if id_docente and id_materia:
                cursor.execute("""
                    SELECT habilitado, fecha_limite, permitir_modificar_pasados, finalizado 
                    FROM tb_docente_permisos_captura
                    WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                """, (id_docente, id_grupo, id_materia))
                permiso = cursor.fetchone()
                
            cursor.execute("""
                SELECT p1_habilitado, p1_fecha_inicio, p1_fecha_fin,
                       p2_habilitado, p2_fecha_inicio, p2_fecha_fin,
                       p3_habilitado, p3_fecha_inicio, p3_fecha_fin,
                       semestral_habilitado, semestral_fecha_inicio, semestral_fecha_fin,
                       extraordinario_habilitado, extraordinario_fecha_inicio, extraordinario_fecha_fin,
                       captura_habilitada, id_nivel_academico
                FROM tb_grupo_periodos_captura WHERE id_grupo = %s
            """, (id_grupo,))
            cfg = cursor.fetchone()

            if is_docente and id_materia:
                # Validar permisos básicos
                perm_res = CalificacionesService.check_captura_permission(id_grupo, id_materia, id_docente, rol)
                if not perm_res['allowed']:
                    solo_lectura = True
                    mensaje_restriccion = perm_res['reason']

            # Bloqueo por semestre si no hay permiso especial activo
            has_active_special_permission = False
            if permiso and permiso.get('habilitado'):
                fecha_limite = permiso.get('fecha_limite')
                hoy = date.today().strftime('%Y-%m-%d')
                if not fecha_limite or hoy <= str(fecha_limite):
                    has_active_special_permission = True

            if is_docente and not has_active_special_permission and cfg and cfg.get('id_nivel_academico') is not None and materia_seleccionada:
                materia_nivel = materia_seleccionada.get('id_nivel_academico')
                if materia_nivel is not None and int(materia_nivel) != int(cfg['id_nivel_academico']):
                    cursor.execute("SELECT nombre FROM tb_niveles_academicos WHERE id = %s", (cfg['id_nivel_academico'],))
                    nivel_row = cursor.fetchone()
                    level_name = nivel_row['nombre'] if nivel_row else f"Nivel {cfg['id_nivel_academico']}"
                    solo_lectura = True
                    mensaje_restriccion = f"La captura para este semestre está deshabilitada. El semestre habilitado es: {level_name}."

            # Armar cct_config
            def is_period_open(enabled, start, end):
                if not enabled:
                    return False
                hoy = date.today().strftime('%Y-%m-%d')
                if start and hoy < str(start):
                    return False
                if end and hoy > str(end):
                    return False
                return True

            cct_config = {
                'captura_p1': True if has_active_special_permission else is_period_open(cfg.get('p1_habilitado', 1) if cfg else 1, cfg.get('p1_fecha_inicio') if cfg else None, cfg.get('p1_fecha_fin') if cfg else None),
                'captura_p2': True if has_active_special_permission else is_period_open(cfg.get('p2_habilitado', 1) if cfg else 1, cfg.get('p2_fecha_inicio') if cfg else None, cfg.get('p2_fecha_fin') if cfg else None),
                'captura_p3': True if has_active_special_permission else is_period_open(cfg.get('p3_habilitado', 1) if cfg else 1, cfg.get('p3_fecha_inicio') if cfg else None, cfg.get('p3_fecha_fin') if cfg else None),
                'captura_semestral': True if has_active_special_permission else is_period_open(cfg.get('semestral_habilitado', 1) if cfg else 1, cfg.get('semestral_fecha_inicio') if cfg else None, cfg.get('semestral_fecha_fin') if cfg else None),
                'captura_extraordinario': True if has_active_special_permission else is_period_open(cfg.get('extraordinario_habilitado', 1) if cfg else 1, cfg.get('extraordinario_fecha_inicio') if cfg else None, cfg.get('extraordinario_fecha_fin') if cfg else None),
            }

            return {
                "grupo": grupo,
                "materias": materias_horario,
                "materiaSeleccionada": materia_seleccionada,
                "idMateriaSeleccionada": int(id_materia) if id_materia else None,
                "alumnos": alumnos_califs,
                "solo_lectura": solo_lectura,
                "mensaje_restriccion": mensaje_restriccion,
                "cct_config": cct_config,
                "finalizado": bool(permiso.get('finalizado')) if permiso else False
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_calificaciones_grupo_materia(id_grupo, id_materia, calificaciones, create_by="SISTEMA", id_docente=None, rol=None, finalizar=False):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Validar permiso antes de guardar si es docente
            if rol and rol.upper() == 'DOCENTE':
                perm_res = CalificacionesService.check_captura_permission(id_grupo, id_materia, id_docente, rol)
                if not perm_res['allowed']:
                    return {"error": perm_res['reason']}

            # 2. Validar rango de calificaciones (0 a 10) para BTI (CCT 2) y BGNE (CCT 3)
            cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo_row = cursor.fetchone()
            id_cct = grupo_row.get("id_centroTrabajo") if grupo_row else None
            
            if id_cct in [2, 3]:
                for item in calificaciones:
                    for fld in ["calificacion", "parcial1", "parcial2", "parcial3", "semestral", "extraordinario"]:
                        val = item.get(fld)
                        if val is not None and val != "":
                            try:
                                f_val = float(val)
                                if f_val < 0.0 or f_val > 10.0:
                                    return {"error": f"La calificacion '{fld}' ({f_val}) esta fuera del rango permitido (0 a 10)."}
                            except ValueError:
                                return {"error": f"La calificacion '{fld}' no es un numero valido."}

            for item in calificaciones:
                id_alumno = item.get("idAlumno")
                calificacion = item.get("calificacion")
                observaciones = item.get("observaciones") or ""
                tipo_acred = item.get("tipoAcreditacion") or "ORDINARIO"

                if not id_alumno or calificacion is None or calificacion == "":
                    continue

                calif_val = float(calificacion)
                
                parcial1 = item.get("parcial1")
                parcial2 = item.get("parcial2")
                parcial3 = item.get("parcial3")
                semestral = item.get("semestral")
                extraordinario = item.get("extraordinario")
                asistencias = item.get("asistencias")
                total_asistencias = item.get("total_asistencias")

                p1_val = float(parcial1) if (parcial1 is not None and parcial1 != "") else None
                p2_val = float(parcial2) if (parcial2 is not None and parcial2 != "") else None
                p3_val = float(parcial3) if (parcial3 is not None and parcial3 != "") else None
                sem_val = float(semestral) if (semestral is not None and semestral != "") else None
                ext_val = float(extraordinario) if (extraordinario is not None and extraordinario != "") else None
                asist_val = int(asistencias) if (asistencias is not None and asistencias != "") else None
                tot_asist_val = int(total_asistencias) if (total_asistencias is not None and total_asistencias != "") else None

                cursor.execute("""
                    SELECT id FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                """, (id_alumno, id_materia, tipo_acred))
                existente = cursor.fetchone()

                if existente:
                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, idGrupo = %s, observaciones = %s, 
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s, 
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calif_val, id_grupo, observaciones, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val, create_by, existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones (
                            idAlumno, idMateria, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy,
                            parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_alumno, id_materia, id_grupo, calif_val, tipo_acred, observaciones, create_by, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val))

            # 3. Registrar como finalizado si corresponde
            if finalizar and id_docente and rol and rol.upper() == 'DOCENTE':
                cursor.execute("""
                    SELECT id FROM tb_docente_permisos_captura 
                    WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                """, (id_docente, id_grupo, id_materia))
                perm = cursor.fetchone()
                if perm:
                    cursor.execute("""
                        UPDATE tb_docente_permisos_captura 
                        SET finalizado = 1, updated_at = NOW() 
                        WHERE id = %s
                    """, (perm['id'],))
                else:
                    cursor.execute("""
                        INSERT INTO tb_docente_permisos_captura (
                            id_docente, id_grupo, id_materia, habilitado, finalizado, created_at, updated_at
                        ) VALUES (%s, %s, %s, 1, 1, NOW(), NOW())
                    """, (id_docente, id_grupo, id_materia))

            conexion.commit()
            return {"success": True, "message": "Calificaciones del grupo guardadas correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
