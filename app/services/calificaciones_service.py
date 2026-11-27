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
    name = name.replace("MET. DE LA INVESTIGACIÃ“N II", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("MET. DE LA INVESTIGACION I", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACIÃ“N I", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACION", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACIÃ“N", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("ECOLOGIA Y MED. AMBIENTE", "ECOLOGIA Y MEDIO AMBIENTE")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MEXICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MÃ‰XICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    name = name.replace("INGLES 1", "INGLES I")
    name = name.replace("INGLES 2", "INGLES II")
    name = name.replace("INGLES 3", "INGLES III")
    name = name.replace("INGLES 4", "INGLES IV")
    name = name.replace("INGLES 5", "INGLES V")
    name = name.replace("INGLES 6", "INGLES VI")
    
    # Force numeric replacements for user prompt matches
    name = name.replace("MATEMATICAS 4", "MATEMATICAS IV")
    name = name.replace("MATEMÃTICAS 4", "MATEMATICAS IV")
    name = name.replace("MATEMATICAS 1", "MATEMATICAS I")
    name = name.replace("MATEMATICAS 2", "MATEMATICAS II")
    name = name.replace("MATEMATICAS 3", "MATEMATICAS III")
    
    name = name.replace("METODO DE LA INVESTIGACION 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODO DE LA INVESTIGACIÃ“N 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODOLOGIA DE LA INVESTIGACION 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODOLOGÃA DE LA INVESTIGACIÃ“N 1", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("METODO DE LA INVESTIGACION 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODO DE LA INVESTIGACIÃ“N 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODOLOGIA DE LA INVESTIGACION 2", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("METODOLOGÃA DE LA INVESTIGACIÃ“N 2", "METODOLOGIA DE LA INVESTIGACION II")
    
    name = name.replace("BIOLOGIA 1", "BIOLOGIA I")
    name = name.replace("BIOLOGÃA 1", "BIOLOGIA I")
    name = name.replace("BIOLOGIA 2", "BIOLOGIA II")
    name = name.replace("BIOLOGÃA 2", "BIOLOGIA II")
    
    name = name.replace("FISICA 1", "FISICA I")
    name = name.replace("FÃSICA 1", "FISICA I")
    name = name.replace("FISICA 2", "FISICA II")
    name = name.replace("FÃSICA 2", "FISICA II")
    
    name = name.replace("LITERATURA 1", "LITERATURA I")
    name = name.replace("LITERATURA 2", "LITERATURA II")
    
    name = name.replace("CONTABILIDAD 1", "CONTABILIDAD I")
    name = name.replace("CONTABILIDAD 2", "CONTABILIDAD II")
    
    name = name.replace("TEMAS SELECTOS DE BIOLOGIA 1", "TEMAS SELECTOS DE BIOLOGIA I")
    name = name.replace("TEMAS SELECTOS DE BIOLOGÃA 1", "TEMAS SELECTOS DE BIOLOGIA I")
    name = name.replace("TEMAS SELECTOS DE BIOLOGIA 2", "TEMAS SELECTOS DE BIOLOGIA II")
    name = name.replace("TEMAS SELECTOS DE BIOLOGÃA 2", "TEMAS SELECTOS DE BIOLOGIA II")
    
    name = name.replace("INFORMATICA 1", "INFORMATICA I")
    name = name.replace("INFORMATICA 2", "INFORMATICA II")
    name = name.replace("INFORMATICA 3", "INFORMATICA III")
    name = name.replace("INFORMATICA 4", "INFORMATICA IV")
    name = name.replace("INFORMÃTICA 1", "INFORMATICA I")
    name = name.replace("INFORMÃTICA 2", "INFORMATICA II")
    name = name.replace("INFORMÃTICA 3", "INFORMATICA III")
    name = name.replace("INFORMÃTICA 4", "INFORMATICA IV")
    
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
        Obtiene el KÃ¡rdex completo del alumno organizado por Periodos/Niveles AcadÃ©micos,
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

            # 2. Obtener los niveles acadÃ©micos correspondientes a este CCT (ej. 1Âº a 6Âº Trimestre o Semestre)
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
                            # Registro duplicado de materia en otro nivel - omitir del kÃ¡rdex
                            continue
                    else:
                        # Materia no canÃ³nica - conservar en su nivel actual
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
                        # La calificación puede estar registrada bajo otra idMateria con el mismo nombre
                        "idMateriaCalificacion": calif["idMateria"] if calif else None,
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

            # Consultar asistencias registradas en tb_asistencias_alumnos (fallback automático; solo pase general)
            from app.services.asistencias_alumnos_service import AsistenciasAlumnosService as _AAS
            cursor.execute(f"""
                SELECT 
                    id_materia,
                    id_nivel_academico,
                    COUNT(*) as total_sesiones,
                    SUM(CASE WHEN estatus IN ('A', 'R') THEN 1 ELSE 0 END) as asistencias_alumno
                FROM tb_asistencias_alumnos
                WHERE id_alumno = %s {_AAS.filtro_pase_general(cursor)}
                GROUP BY id_materia, id_nivel_academico
            """, (id_alumno,))
            asist_fallbacks = {}
            for ar in (cursor.fetchall() or []):
                asist_fallbacks[(ar["id_materia"], ar["id_nivel_academico"])] = {
                    "asistencias": int(ar["asistencias_alumno"] or 0),
                    "total_asistencias": int(ar["total_sesiones"] or 0)
                }

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

                    asist_num = int(mat["asistencias"]) if mat.get("asistencias") is not None else None
                    tot_asist_num = int(mat["total_asistencias"]) if mat.get("total_asistencias") is not None else None

                    if asist_num is None and tot_asist_num is None:
                        fb = asist_fallbacks.get((mat["idMateria"], id_nivel))
                        if fb and fb["total_asistencias"] > 0:
                            asist_num = fb["asistencias"]
                            tot_asist_num = fb["total_asistencias"]

                    lista_materias_periodo.append({
                        "idMateria": mat["idMateria"],
                        "nombreMateria": mat["nombreMateria"],
                        "claveMateria": mat["claveMateria"],
                        "idCalificacion": mat["idCalificacion"],
                        "idMateriaCalificacion": mat.get("idMateriaCalificacion"),
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
                        "asistencias": asist_num,
                        "total_asistencias": tot_asist_num,
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

            # Obtener fechas de periodos de evaluación configuradas para el grupo del alumno (solo aplica a CCT BTI)
            periodos_evaluacion = None
            if alumno.get("idGrupo") and not is_bgne:
                cursor.execute("""
                    SELECT 
                        p1_fecha_inicio, p1_fecha_fin,
                        p2_fecha_inicio, p2_fecha_fin,
                        p3_fecha_inicio, p3_fecha_fin,
                        semestral_fecha_inicio, semestral_fecha_fin,
                        extraordinario_fecha_inicio, extraordinario_fecha_fin
                    FROM tb_grupo_periodos_captura
                    WHERE id_grupo = %s
                """, (alumno["idGrupo"],))
                g_conf = cursor.fetchone()
                if g_conf:
                    def fmt_date(d):
                        if not d:
                            return None
                        if isinstance(d, (date, datetime)):
                            return d.strftime('%d/%m/%Y')
                        d_str = str(d).strip()
                        if len(d_str) >= 10 and '-' in d_str[:10]:
                            parts = d_str[:10].split('-')
                            if len(parts) == 3:
                                return f"{parts[2]}/{parts[1]}/{parts[0]}"
                        return d_str

                    def fmt_range(ini, fin):
                        d_ini = fmt_date(ini)
                        d_fin = fmt_date(fin)
                        if d_ini and d_fin:
                            return f"{d_ini} al {d_fin}"
                        elif d_ini:
                            return f"Desde {d_ini}"
                        elif d_fin:
                            return f"Hasta {d_fin}"
                        return None

                    periodos_evaluacion = {
                        "p1_inicio": fmt_date(g_conf.get("p1_fecha_inicio")),
                        "p1_fin": fmt_date(g_conf.get("p1_fecha_fin")),
                        "p1_rango": fmt_range(g_conf.get("p1_fecha_inicio"), g_conf.get("p1_fecha_fin")),
                        "p2_inicio": fmt_date(g_conf.get("p2_fecha_inicio")),
                        "p2_fin": fmt_date(g_conf.get("p2_fecha_fin")),
                        "p2_rango": fmt_range(g_conf.get("p2_fecha_inicio"), g_conf.get("p2_fecha_fin")),
                        "p3_inicio": fmt_date(g_conf.get("p3_fecha_inicio")),
                        "p3_fin": fmt_date(g_conf.get("p3_fecha_fin")),
                        "p3_rango": fmt_range(g_conf.get("p3_fecha_inicio"), g_conf.get("p3_fecha_fin")),
                        "semestral_inicio": fmt_date(g_conf.get("semestral_fecha_inicio")),
                        "semestral_fin": fmt_date(g_conf.get("semestral_fecha_fin")),
                        "semestral_rango": fmt_range(g_conf.get("semestral_fecha_inicio"), g_conf.get("semestral_fecha_fin")),
                        "extraordinario_inicio": fmt_date(g_conf.get("extraordinario_fecha_inicio")),
                        "extraordinario_fin": fmt_date(g_conf.get("extraordinario_fecha_fin")),
                        "extraordinario_rango": fmt_range(g_conf.get("extraordinario_fecha_inicio"), g_conf.get("extraordinario_fecha_fin")),
                    }

            # Asistencias por parcial (BTI) capturadas en Captura de Calificaciones; las usa la boleta
            asistencias_parciales = {}
            if not is_bgne:
                asistencias_parciales = CalificacionesService.get_asistencias_parciales_alumno(cursor, id_alumno)

            return {
                "alumno": alumno,
                "periodos": kardex_periodos,
                "promedioGeneral": promedio_general,
                "totalMateriasEvaluadas": total_materias_evaluadas,
                "periodosEvaluacion": periodos_evaluacion,
                "asistenciasParciales": asistencias_parciales
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

                if calificacion is None or calificacion == "" or str(calificacion).strip().lower() == "null":
                    # Si la calificacion se envia vacia o null, eliminar la calificacion si existe
                    cursor.execute("""
                        DELETE FROM tb_calificaciones 
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                    """, (id_alumno, id_materia, tipo_acred))
                    continue

                # Verificar si ya existe calificación para este alumno y materia. Ordinario y extraordinario
                # comparten renglón, así que no se filtra por tipo exacto (evita duplicar el registro).
                if str(tipo_acred).upper() == "EQUIVALENCIA":
                    cursor.execute("""
                        SELECT id, parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        FROM tb_calificaciones
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = 'EQUIVALENCIA'
                    """, (id_alumno, id_materia))
                else:
                    cursor.execute("""
                        SELECT id, parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        FROM tb_calificaciones
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                        ORDER BY id ASC
                    """, (id_alumno, id_materia))
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
                    # Si un campo no viene en el item (ej. actualización desde Kárdex), conservar el valor existente en BD
                    p1_final = p1_val if "parcial1" in item else existente.get("parcial1")
                    p2_final = p2_val if "parcial2" in item else existente.get("parcial2")
                    p3_final = p3_val if "parcial3" in item else existente.get("parcial3")
                    sem_final = sem_val if "semestral" in item else existente.get("semestral")
                    ext_final = ext_val if "extraordinario" in item else existente.get("extraordinario")
                    asist_final = asist_val if "asistencias" in item else existente.get("asistencias")
                    tot_asist_final = tot_asist_val if "total_asistencias" in item else existente.get("total_asistencias")

                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, tipoAcreditacion = %s, id_nivel_academico = %s, idGrupo = COALESCE(%s, idGrupo), observaciones = COALESCE(%s, observaciones),
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s,
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calificacion, tipo_acred, id_nivel, id_grupo, observaciones, p1_final, p2_final, p3_final, sem_final, ext_final, asist_final, tot_asist_final, create_by, existente["id"]))
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
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _a_fecha(v):
        """date/datetime o texto 'YYYY-MM-DD...' → date (None si no se puede)."""
        if not v:
            return None
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(str(v)[:10], '%Y-%m-%d').date()
        except ValueError:
            return None

    @staticmethod
    def trimestres_grupo(fecha_inicio, fecha_fin):
        """
        Calendario de trimestres BGNE (mismo que Horarios): 13 semanas desde la fecha de inicio del grupo,
        el siguiente inicia una semana después del fin del anterior, hasta la fecha fin del grupo.
        Cada trimestre: {'nivel', 'inicio', 'fin' (tope en la fecha fin del grupo), 'captura_fin' (fin + 6 días)}.
        """
        from datetime import timedelta
        inicio = CalificacionesService._a_fecha(fecha_inicio)
        fin_grupo = CalificacionesService._a_fecha(fecha_fin)
        if not inicio:
            return []
        trimestres = []
        ini = inicio
        for nivel in range(1, 7):
            if fin_grupo and ini > fin_grupo:
                break
            fin_trim = ini + timedelta(days=12 * 7)   # 13 semanas
            fin_real = min(fin_trim, fin_grupo) if fin_grupo else fin_trim
            trimestres.append({'nivel': nivel, 'inicio': ini, 'fin': fin_real, 'captura_fin': fin_real + timedelta(days=6)})
            if fin_grupo and fin_trim >= fin_grupo:
                break
            ini = fin_trim + timedelta(days=7)
        return trimestres

    @staticmethod
    def ventanas_bgne(fecha_inicio, fecha_fin, fin_manual=None, inicio_manual=None):
        """
        Ventanas de captura BGNE de todos los trimestres: [{'nivel', 'apertura', 'cierre'}].
        Abren el último día del trimestre y cierran 6 días después. Las fechas manuales
        (p1_* de "Periodos por grupo") solo pueden alargar el cierre de una ventana: la fecha fin
        manual extiende la última ventana que abrió antes de ella, siempre que el rango manual
        no tenga inicio o empiece dentro de esa ventana. Nunca adelantan la apertura.
        """
        fin_manual = CalificacionesService._a_fecha(fin_manual)
        inicio_manual = CalificacionesService._a_fecha(inicio_manual)
        ventanas = [{'nivel': t['nivel'], 'apertura': t['fin'], 'cierre': t['captura_fin']}
                    for t in CalificacionesService.trimestres_grupo(fecha_inicio, fecha_fin)]
        if fin_manual:
            previas = [v for v in ventanas if v['apertura'] <= fin_manual]
            v = previas[-1] if previas else None
            if v and fin_manual > v['cierre'] and (not inicio_manual or inicio_manual <= v['cierre']):
                v['cierre'] = fin_manual
        return ventanas

    @staticmethod
    def p1_abierto_bgne(grupo, cfg, has_prorroga=False, hoy=None):
        """Calificación final BGNE: abierta si hoy cae en la ventana automática (o extendida) o hay prórroga vigente."""
        cfg = cfg or {}
        if cfg.get('p1_habilitado') is not None and not cfg.get('p1_habilitado'):
            return False
        if has_prorroga:
            return True
        v = CalificacionesService.ventana_captura_bgne(grupo.get('fechaInicio'), grupo.get('fechaFin'), hoy,
                                                       fin_manual=cfg.get('p1_fecha_fin'), inicio_manual=cfg.get('p1_fecha_inicio'))
        return bool(v and v['abierta'])

    @staticmethod
    def ventana_captura_bgne(fecha_inicio, fecha_fin, hoy=None, fin_manual=None, inicio_manual=None):
        """
        Regla BGNE: la calificación de cada trimestre se captura en la semana que sigue a su fin,
        desde el día en que termina el trimestre hasta 6 días después (antes de que inicie el siguiente).
        La fecha fin manual solo extiende el cierre (ver ventanas_bgne).
        Trimestres con el mismo calendario de Horarios: 13 semanas desde la fecha de inicio del grupo,
        el siguiente inicia una semana después del fin del anterior, hasta la fecha fin del grupo.
        Devuelve {'nivel', 'apertura', 'cierre', 'abierta'} de la ventana que corresponde a hoy:
        la abierta; si no hay, la próxima; si ya pasaron todas, la última. None si el grupo no tiene fechas.
        """
        hoy = hoy or date.today()
        ventanas = CalificacionesService.ventanas_bgne(fecha_inicio, fecha_fin, fin_manual, inicio_manual)
        if not ventanas:
            return None

        for v in ventanas:
            if v['apertura'] <= hoy <= v['cierre']:
                return {**v, 'abierta': True}
        proxima = next((v for v in ventanas if v['apertura'] > hoy), None)
        anteriores = [v for v in ventanas if v['cierre'] < hoy]
        return {**(proxima or ventanas[-1]), 'abierta': False, 'anterior': anteriores[-1] if anteriores else None}

    # Observaciones por etapa de captura (script 2026-11-26_calificaciones_observaciones_por_parcial.sql)
    OBS_COLUMNAS = {'p1': 'obs_parcial1', 'p2': 'obs_parcial2', 'p3': 'obs_parcial3',
                    'semestral': 'obs_semestral', 'extraordinario': 'obs_extraordinario'}
    _obs_por_periodo_disponible = None

    @staticmethod
    def obs_por_periodo_disponible(cursor):
        """True si tb_calificaciones ya tiene las columnas obs_* (se consulta una vez por proceso)."""
        if CalificacionesService._obs_por_periodo_disponible is None:
            cursor.execute("SHOW COLUMNS FROM tb_calificaciones LIKE 'obs\\_extraordinario'")
            CalificacionesService._obs_por_periodo_disponible = cursor.fetchone() is not None
        return CalificacionesService._obs_por_periodo_disponible

    @staticmethod
    def periodo_observaciones(cursor, id_grupo, hoy=None, prorroga_periodo=None):
        """
        Etapa cuyas observaciones se muestran y guardan en la captura: la habilitada hoy.
          - BGNE: extraordinario si su ventana configurada está abierta; si no, la calificación final (p1).
          - BTI: el periodo habilitado con fechas que incluye hoy (el último si hay varios); si ninguno,
            el periodo de la prórroga vigente del docente (prorroga_periodo); si no,
            el último que ya inició (sus observaciones se siguen viendo hasta que abre el siguiente); si no, p1.
        Devuelve {'clave', 'nombre'}.
        """
        a_fecha = CalificacionesService._a_fecha
        hoy = hoy or date.today()
        cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
        es_bgne = int((cursor.fetchone() or {}).get('id_centroTrabajo') or 0) == 3
        cursor.execute("SELECT * FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
        cfg = cursor.fetchone() or {}

        def rango(p):
            hab = cfg.get(f'{p}_habilitado')
            if hab is not None and not hab:
                return None, None
            return a_fecha(cfg.get(f'{p}_fecha_inicio')), a_fecha(cfg.get(f'{p}_fecha_fin'))

        nombres = {'p1': 'Calificación final' if es_bgne else 'Parcial 1', 'p2': 'Parcial 2', 'p3': 'Parcial 3',
                   'semestral': 'Semestral', 'extraordinario': 'Extraordinario'}
        if es_bgne:
            ini, fin = rango('extraordinario')
            clave = 'extraordinario' if (ini and fin and ini <= hoy <= fin) else 'p1'
        else:
            orden = ('p1', 'p2', 'p3', 'semestral', 'extraordinario')
            abiertos = [p for p in orden if rango(p)[0] and rango(p)[1] and rango(p)[0] <= hoy <= rango(p)[1]]
            if abiertos:
                clave = abiertos[-1]
            elif prorroga_periodo in orden:
                clave = prorroga_periodo
            else:
                iniciados = [(rango(p)[0], i, p) for i, p in enumerate(orden) if rango(p)[0] and rango(p)[0] <= hoy]
                clave = max(iniciados)[2] if iniciados else 'p1'
        return {'clave': clave, 'nombre': nombres[clave]}

    PERIODOS_BTI = ('p1', 'p2', 'p3', 'semestral', 'extraordinario')
    NOMBRES_PERIODO_BTI = {'p1': '1er parcial', 'p2': '2do parcial', 'p3': '3er parcial',
                           'semestral': 'examen semestral', 'extraordinario': 'extraordinario'}
    _envios_disponible = None

    @staticmethod
    def envios_disponible(cursor):
        """True si ya existe tb_docente_envios_captura (scripts/2026-11-26_envios_captura_por_periodo.sql)."""
        if not CalificacionesService._envios_disponible:
            cursor.execute("SHOW TABLES LIKE 'tb\\_docente\\_envios\\_captura'")
            CalificacionesService._envios_disponible = cursor.fetchone() is not None
        return CalificacionesService._envios_disponible

    @staticmethod
    def periodos_enviados(cursor, id_docente, id_grupo, id_materia):
        """Periodos BTI cuyas calificaciones ya envió el docente en esa asignatura y grupo (quedan bloqueados).
        Un envío sin ninguna calificación en ese periodo (se envió vacío o después se borraron todas)
        no cuenta: es como si no se hubiera capturado.
        Devuelve {periodo: fecha y hora del último envío}."""
        if not id_docente or not CalificacionesService.envios_disponible(cursor):
            return {}
        cursor.execute("""
            SELECT periodo, enviado_at FROM tb_docente_envios_captura
            WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
        """, (id_docente, id_grupo, id_materia))
        envios = {r['periodo']: r['enviado_at'] for r in cursor.fetchall()}
        columnas = {'p1': 'parcial1', 'p2': 'parcial2', 'p3': 'parcial3',
                    'semestral': 'semestral', 'extraordinario': 'extraordinario'}
        for p in list(envios):
            col = columnas.get(p)
            if not col:
                continue
            cursor.execute(f"""
                SELECT 1 FROM tb_calificaciones c
                JOIN tb_alumnogrupo ag ON ag.idAlumno = c.idAlumno AND ag.idGrupo = %s AND ag.estado = 'ACTIVO'
                WHERE c.idMateria = %s AND c.{col} IS NOT NULL AND c.tipoAcreditacion != 'EQUIVALENCIA'
                LIMIT 1
            """, (id_grupo, id_materia))   # nombre de columna de una lista fija
            if cursor.fetchone() is None:
                del envios[p]
        return envios

    @staticmethod
    def periodo_solo_faltantes(permiso, enviados, hoy=None):
        """Periodo ya enviado que la prórroga vigente reabre SOLO para los alumnos sin calificación
        (las ya enviadas siguen bloqueadas). Deja de aplicar en cuanto el docente vuelve a enviar
        después de otorgada (o editada) la prórroga. None si no aplica."""
        p = CalificacionesService.periodo_prorroga_vigente(permiso, hoy)
        if not p or p not in enviados:
            return None
        otorgada = permiso.get('updated_at') or permiso.get('created_at')
        enviado = enviados.get(p)
        if otorgada and enviado and enviado >= otorgada:
            return None   # ya volvió a enviar con la prórroga
        return p

    @staticmethod
    def periodo_prorroga_vigente(permiso, hoy=None):
        """Periodo de la prórroga del docente si está vigente (habilitada, no finalizada y antes de su fecha límite).
        None si no hay prórroga vigente o si no indica periodo (aplica a todos, como antes)."""
        hoy = hoy or date.today().strftime('%Y-%m-%d')
        if not (permiso and permiso.get('habilitado') and not permiso.get('finalizado')
                and permiso.get('fecha_limite') and hoy <= str(permiso.get('fecha_limite'))):
            return None
        p = permiso.get('periodo')
        return p if p in CalificacionesService.PERIODOS_BTI else None

    @staticmethod
    def periodo_bti_abierto(cfg, periodo, has_prorroga=False, hoy=None, prorroga_periodo=None):
        """
        Regla BTI: todo es manual. El admin indica en "Periodos por grupo" la fecha de inicio y fin de cada periodo.
        Un periodo está abierto solo si está habilitado y hoy cae entre su fecha de inicio y fin.
        Prórroga vigente con periodo (prorroga_periodo): abre solo ese periodo para el docente, aunque esté
        cerrado en el grupo; los demás siguen la regla normal.
        Prórroga vigente sin periodo (anteriores al cambio): basta con que el periodo no esté
        desactivado y ya haya iniciado (si tiene fecha de inicio).
        Sin prórroga, sin configuración o sin fechas, el periodo está cerrado.
        """
        cfg = cfg or {}
        habilitado = cfg.get(f'{periodo}_habilitado')
        hoy = hoy or date.today().strftime('%Y-%m-%d')
        ini = str(cfg[f'{periodo}_fecha_inicio'])[:10] if cfg.get(f'{periodo}_fecha_inicio') else None
        fin = str(cfg[f'{periodo}_fecha_fin'])[:10] if cfg.get(f'{periodo}_fecha_fin') else None
        if has_prorroga and prorroga_periodo:
            if periodo == prorroga_periodo:
                return True
            has_prorroga = False
        if has_prorroga:
            desactivado = habilitado is not None and not habilitado
            return not desactivado and (not ini or hoy >= ini)
        # Igual que "Docentes pendientes": habilitado sin valor cuenta como activo si tiene fechas
        return bool((habilitado is None or habilitado) and ini and fin and ini <= hoy <= fin)

    @staticmethod
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
                    'reason': 'IdentificaciÃ³n de docente no encontrada.'
                }

            hoy = date.today().strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT * 
                FROM tb_docente_permisos_captura
                WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
            """, (id_docente, id_grupo, id_materia))
            permiso = cursor.fetchone()

            # BTI bloquea por periodo enviado (tb_docente_envios_captura), no la asignatura completa:
            # el marcador "finalizado" de envíos anteriores al cambio no aplica en BTI.
            cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            es_bti_grupo = int((cursor.fetchone() or {}).get('id_centroTrabajo') or 0) == 2

            if permiso and not es_bti_grupo and (permiso.get('finalizado') == 1 or permiso.get('finalizado') is True):
                return {
                    'allowed': False,
                    'reason': 'Las calificaciones de esta asignatura ya fueron enviadas y confirmadas. Solo el administrador puede realizar cambios.'
                }

            if permiso and not permiso.get('habilitado'):
                return {
                    'allowed': False,
                    'reason': 'La captura de calificaciones ha sido deshabilitada para esta asignatura por administraciÃ³n.'
                }

            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM tb_horarios
                    WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                ) AS exist
            """, (id_docente, id_grupo, id_materia))
            horario_exist = cursor.fetchone()
            horario_asignado = bool(horario_exist and horario_exist.get('exist'))

            if not permiso and not horario_asignado:
                return {
                    'allowed': False,
                    'reason': 'No tienes asignada esta asignatura en este grupo.'
                }

            cursor.execute("SELECT statusGrupo, fechaInicio, fechaFin, id_nivel_academico, id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo = cursor.fetchone()
            
            cursor.execute("SELECT id_nivel_academico FROM tb_materias WHERE id = %s", (id_materia,))
            materia = cursor.fetchone()

            if not grupo:
                return {
                    'allowed': False,
                    'reason': 'El grupo no existe.'
                }

            cursor.execute("SELECT captura_habilitada FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
            grp_config = cursor.fetchone()
            if grp_config and grp_config.get('captura_habilitada') is not None and not grp_config.get('captura_habilitada'):
                has_prorroga_vigente = (
                    permiso and permiso.get('habilitado') and
                    not permiso.get('finalizado') and
                    permiso.get('fecha_limite') and
                    hoy <= str(permiso.get('fecha_limite'))
                )
                if not has_prorroga_vigente:
                    return {
                        'allowed': False,
                        'reason': 'Captura bloqueada por la administración.'
                    }

            # BGNE: ventana automática al terminar cada trimestre (último día de clases + 6 días).
            # Una fecha fin manual en "Periodos por grupo" solo alarga el cierre; nunca abre antes.
            # No aplica si el docente tiene prórroga vigente o si está abierta la ventana configurada de extraordinario.
            if int(grupo.get('id_centroTrabajo') or 0) == 3:
                cursor.execute("""
                    SELECT p1_habilitado, p1_fecha_inicio, p1_fecha_fin,
                           extraordinario_habilitado, extraordinario_fecha_inicio, extraordinario_fecha_fin
                    FROM tb_grupo_periodos_captura WHERE id_grupo = %s
                """, (id_grupo,))
                cfg_b = cursor.fetchone() or {}
                prorroga_vigente = bool(
                    permiso and permiso.get('habilitado') and not permiso.get('finalizado') and
                    permiso.get('fecha_limite') and hoy <= str(permiso.get('fecha_limite'))
                )
                ext_abierto = bool(
                    cfg_b.get('extraordinario_habilitado') and
                    cfg_b.get('extraordinario_fecha_inicio') and cfg_b.get('extraordinario_fecha_fin') and
                    str(cfg_b['extraordinario_fecha_inicio']) <= hoy <= str(cfg_b['extraordinario_fecha_fin'])
                )
                if not prorroga_vigente and not ext_abierto:
                    if cfg_b.get('p1_habilitado') is not None and not cfg_b.get('p1_habilitado'):
                        return {'allowed': False, 'reason': 'Captura bloqueada por la administración.'}
                    v = CalificacionesService.ventana_captura_bgne(grupo.get('fechaInicio'), grupo.get('fechaFin'),
                                                                   fin_manual=cfg_b.get('p1_fecha_fin'),
                                                                   inicio_manual=cfg_b.get('p1_fecha_inicio'))
                    if v and not v['abierta']:
                        # Fuera de la ventana del trimestre: mismo mensaje corto que BTI
                        return {'allowed': False, 'reason': 'Captura bloqueada por la administración.'}

            # BTI: solo con un periodo habilitado manualmente cuyas fechas incluyan hoy (o prórroga vigente).
            # Misma regla que al abrir la captura y al guardar, para que "Mis grupos" no ofrezca capturar de más.
            if int(grupo.get('id_centroTrabajo') or 0) == 2:
                cursor.execute("SELECT * FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
                cfg_t = cursor.fetchone() or {}
                prorroga_vigente = bool(
                    permiso and permiso.get('habilitado') and not permiso.get('finalizado') and
                    permiso.get('fecha_limite') and hoy <= str(permiso.get('fecha_limite'))
                )
                prorroga_periodo = CalificacionesService.periodo_prorroga_vigente(permiso, hoy)
                periodos = ('p1', 'p2', 'p3', 'semestral', 'extraordinario')
                if not any(CalificacionesService.periodo_bti_abierto(cfg_t, p, prorroga_vigente, prorroga_periodo=prorroga_periodo) for p in periodos):
                    # Ningún periodo abierto (cerró, aún no abre o sin fechas): mensaje único, sin detalles que confundan
                    return {'allowed': False, 'reason': "Captura bloqueada por la administración."}

                # Periodo ya enviado por el docente: queda bloqueado (no se edita ni se reenvía)
                abiertos = [p for p in periodos if CalificacionesService.periodo_bti_abierto(cfg_t, p, prorroga_vigente, prorroga_periodo=prorroga_periodo)]
                enviados = CalificacionesService.periodos_enviados(cursor, id_docente, id_grupo, id_materia)
                # La prórroga de un periodo enviado lo reabre solo para los alumnos sin calificación
                faltantes = CalificacionesService.periodo_solo_faltantes(permiso, enviados, hoy)
                if abiertos and all(p in enviados and p != faltantes for p in abiertos):
                    etapas = ', '.join(CalificacionesService.NOMBRES_PERIODO_BTI[p] for p in abiertos)
                    return {'allowed': False,
                            'reason': f"Ya enviaste las calificaciones del {etapas}; quedaron registradas y no se pueden modificar."}

            if grupo.get('statusGrupo') and grupo.get('statusGrupo').upper() != 'ACTIVO':
                if not permiso or not permiso.get('permitir_modificar_pasados'):
                    return {
                        'allowed': False,
                        'reason': 'El grupo se encuentra inactivo. Requiere autorización especial de administración.'
                    }

            # Si la asignatura está en tb_horarios asignada para este grupo, es una materia activa del grupo y no se bloquea por nivel
            if grupo and materia and not horario_asignado:
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

            # Prórroga BTI de un periodo: al vencer solo deja de abrir ese periodo (los demás siguen sus fechas)
            prorroga_de_periodo = int(grupo.get('id_centroTrabajo') or 0) == 2 and permiso and \
                permiso.get('periodo') in CalificacionesService.PERIODOS_BTI
            if permiso and permiso.get('fecha_limite') and not prorroga_de_periodo:
                fecha_limite_str = str(permiso.get('fecha_limite'))
                if hoy > fecha_limite_str:
                    return {
                        'allowed': False,
                        'reason': f"El periodo extraordinario de captura expiró el {datetime.strptime(fecha_limite_str, '%Y-%m-%d').strftime('%d/%m/%Y')}."
                    }
            else:
                # Si el grupo no está ACTIVO, validar fechaFin
                if grupo.get('statusGrupo') and grupo.get('statusGrupo').upper() != 'ACTIVO' and grupo.get('fechaFin'):
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
            # 1. InformaciÃ³n del grupo
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

            # 2. Obtener materias y docentes asociados a este grupo
            id_cct_grupo = grupo.get("id_centro_trabajo") or grupo.get("id_centroTrabajo") or 3
            is_docente = rol and rol.upper() == 'DOCENTE'
            group_level = grupo.get("id_nivel_academico")
            is_bti = (int(id_cct_grupo) == 2)

            # A) Horarios y docentes asignados en tb_horarios para este grupo
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
            materias_horario_db = cursor.fetchall()

            if is_docente and id_docente:
                # Si es rol DOCENTE: incluir las materias asignadas a este docente en tb_horarios para este grupo
                filtered_materias = [
                    m for m in materias_horario_db
                    if m.get("id_docente") is not None and int(m["id_docente"]) == int(id_docente)
                ]
                materias_horario = filtered_materias
            else:
                # Para Administrador y Control Escolar:
                # Todas las materias activas declaradas para el CCT siempre deben estar disponibles (todos los semestres/trimestres)
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
                    WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
                      AND (m.estatusMateria = 'ACTIVA' OR m.estatusMateria IS NULL)
                    ORDER BY na.numero ASC, ordenMateria ASC
                """, (id_cct_grupo,))
                todas_materias_cct = cursor.fetchall()

                # Mapear las materias que ya tienen docente asignado en tb_horarios
                mapa_horarios = {m["idMateria"]: m for m in materias_horario_db}

                lista_combinada = []
                ids_procesados = set()

                for m in todas_materias_cct:
                    mid = m["idMateria"]
                    if mid in mapa_horarios:
                        lista_combinada.append(mapa_horarios[mid])
                    else:
                        lista_combinada.append(m)
                    ids_procesados.add(mid)

                # Mantener cualquier materia adicional que pudiera estar en tb_horarios
                for m in materias_horario_db:
                    if m["idMateria"] not in ids_procesados:
                        lista_combinada.append(m)
                        ids_procesados.add(m["idMateria"])

                materias_horario = sorted(
                    lista_combinada,
                    key=lambda x: (
                        x.get("numeroNivel") if x.get("numeroNivel") is not None else 99,
                        x.get("ordenMateria") if x.get("ordenMateria") is not None else x.get("idMateria", 0)
                    )
                )

            # Si se proporcionÃ³ id_materia pero no pertenece a las materias del grupo (p. ej. en BTI), reajustar
            if id_materia and materias_horario:
                if not any(str(m["idMateria"]) == str(id_materia) for m in materias_horario):
                    id_materia = None

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
                    mats_mismo_nivel = [m["idMateria"] for m in materias_horario if group_level is not None and m.get("id_nivel_academico") == group_level]
                    if mats_mismo_nivel:
                        id_materia = mats_mismo_nivel[0]
                    else:
                        id_materia = materias_horario[0]["idMateria"]

            # Docente de la materia seleccionada
            materia_seleccionada = None
            for m in materias_horario:
                if str(m["idMateria"]) == str(id_materia):
                    materia_seleccionada = m
                    break

            # Si el rol es DOCENTE y id_materia no estÃ¡ en materias_horario, reajustarla
            if is_docente and id_docente and id_materia and not materia_seleccionada:
                for m in materias_horario:
                    if str(m["idMateria"]) == str(id_materia) and m.get("id_docente") is not None and int(m["id_docente"]) == int(id_docente):
                        materia_seleccionada = m
                        break

            # 3. Lista de alumnos del grupo con sus calificaciones en esta materia
            alumnos_califs = []
            periodo_obs = None
            if id_materia:
                # Obtener el nÃºmero de nivel de la materia actual
                numero_nivel_materia = 1
                if materia_seleccionada and materia_seleccionada.get("numeroNivel") is not None:
                    numero_nivel_materia = int(materia_seleccionada["numeroNivel"])
                else:
                    cursor.execute("SELECT numero FROM tb_niveles_academicos WHERE id = (SELECT id_nivel_academico FROM tb_materias WHERE id = %s)", (id_materia,))
                    nivel_row = cursor.fetchone()
                    if nivel_row and nivel_row.get("numero") is not None:
                        numero_nivel_materia = int(nivel_row["numero"])

                # Observaciones del parcial habilitado (si ya existen las columnas por parcial)
                obs_col = None
                if CalificacionesService.obs_por_periodo_disponible(cursor):
                    prorroga_obs = None
                    if id_docente:
                        cursor.execute("""
                            SELECT * FROM tb_docente_permisos_captura
                            WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                        """, (id_docente, id_grupo, id_materia))
                        prorroga_obs = CalificacionesService.periodo_prorroga_vigente(cursor.fetchone())
                    periodo_obs = CalificacionesService.periodo_observaciones(cursor, id_grupo, prorroga_periodo=prorroga_obs)
                    obs_col = CalificacionesService.OBS_COLUMNAS[periodo_obs['clave']]

                cursor.execute(f"""
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
                        {f'c.{obs_col}' if obs_col else 'c.observaciones'} AS observaciones,
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
                    WHERE a.idGrupo = %s AND a.statusAlumno = 'ACTIVO'
                    ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
                """, (id_materia, id_grupo))
                alumnos_califs = cursor.fetchall()

                # Determinar si cada alumno tiene estatus de equivalencia para este periodo
                for a in alumnos_califs:
                    is_equiv = False
                    # Se considera equivalencia si ya estÃ¡ registrado explÃ­citamente como EQUIVALENCIA
                    if str(a.get("tipoAcreditacion") or "").upper() == "EQUIVALENCIA":
                        is_equiv = True
                    a["es_equivalencia"] = is_equiv

            # 4. LÃ³gica de permisos de captura
            solo_lectura = False
            mensaje_restriccion = ""
            
            permiso = None
            if id_docente and id_materia:
                cursor.execute("""
                    SELECT * 
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

            # Prórroga especial activa para este docente/asignatura (en BTI, para un periodo)
            hoy = date.today().strftime('%Y-%m-%d')
            prorroga_periodo = CalificacionesService.periodo_prorroga_vigente(permiso, hoy)
            has_active_special_permission = False
            if permiso and permiso.get('habilitado') and not permiso.get('finalizado'):
                fecha_limite = permiso.get('fecha_limite')
                if fecha_limite and hoy <= str(fecha_limite):
                    has_active_special_permission = True

            # Bloqueo explícito del grupo por el administrador
            if is_docente and cfg and cfg.get('captura_habilitada') is not None and not cfg.get('captura_habilitada') and not has_active_special_permission:
                solo_lectura = True
                if not mensaje_restriccion:
                    mensaje_restriccion = "Captura bloqueada por la administración."

            # Bloqueo por semestre si no hay permiso especial activo
            # (No bloquear si la materia está formalmente asignada al docente en tb_horarios para este grupo)
            is_horario_assigned = any(int(m["idMateria"]) == int(id_materia) for m in materias_horario_db if m.get("id_docente") and int(m["id_docente"]) == int(id_docente)) if (id_materia and is_docente and id_docente) else False
            if is_docente and not has_active_special_permission and not is_horario_assigned and cfg and cfg.get('id_nivel_academico') is not None and materia_seleccionada:
                materia_nivel = materia_seleccionada.get('id_nivel_academico')
                if materia_nivel is not None and int(materia_nivel) != int(cfg['id_nivel_academico']):
                    cursor.execute("SELECT nombre FROM tb_niveles_academicos WHERE id = %s", (cfg['id_nivel_academico'],))
                    nivel_row = cursor.fetchone()
                    level_name = nivel_row['nombre'] if nivel_row else f"Nivel {cfg['id_nivel_academico']}"
                    solo_lectura = True
                    mensaje_restriccion = f"La captura para este semestre está deshabilitada. El semestre habilitado es: {level_name}."

            # Armar cct_config
            def is_period_open(enabled, start, end, has_prorroga=False):
                if not enabled:
                    return False
                hoy_str = date.today().strftime('%Y-%m-%d')
                if start and hoy_str < str(start):
                    return False
                if end and hoy_str > str(end):
                    if not has_prorroga:
                        return False
                return True

            periodos_enviados_resp = []
            periodo_solo_faltantes_resp = None
            if is_bti:
                # BTI: la captura solo se abre manualmente desde "Periodos por grupo" (periodo habilitado y con fechas).
                bloqueado = bool(cfg and cfg.get('captura_habilitada') is not None and not cfg.get('captura_habilitada')
                                 and not has_active_special_permission)
                # El docente no edita los periodos que ya envió; con prórroga de ese periodo, solo captura los faltantes
                enviados = (CalificacionesService.periodos_enviados(cursor, id_docente, id_grupo, id_materia)
                            if is_docente and id_materia else {})
                solo_faltantes = CalificacionesService.periodo_solo_faltantes(permiso, enviados, hoy) if is_docente else None
                cct_config = {
                    f'captura_{p}': (not bloqueado) and (p not in enviados or p == solo_faltantes)
                                    and CalificacionesService.periodo_bti_abierto(cfg, p, has_active_special_permission, prorroga_periodo=prorroga_periodo)
                    for p in CalificacionesService.PERIODOS_BTI
                }
                periodos_enviados_resp = sorted(enviados, key=CalificacionesService.PERIODOS_BTI.index)
                periodo_solo_faltantes_resp = solo_faltantes
            elif not cfg:
                cct_config = {
                    'captura_p1': True,
                    'captura_p2': True,
                    'captura_p3': True,
                    'captura_semestral': True,
                    'captura_extraordinario': True,
                }
            elif cfg.get('captura_habilitada') is not None and not cfg.get('captura_habilitada') and not has_active_special_permission:
                cct_config = {
                    'captura_p1': False,
                    'captura_p2': False,
                    'captura_p3': False,
                    'captura_semestral': False,
                    'captura_extraordinario': False,
                }
            else:
                p1_en = cfg.get('p1_habilitado') if cfg.get('p1_habilitado') is not None else 1
                p2_en = cfg.get('p2_habilitado') if cfg.get('p2_habilitado') is not None else 1
                p3_en = cfg.get('p3_habilitado') if cfg.get('p3_habilitado') is not None else 1
                sem_en = cfg.get('semestral_habilitado') if cfg.get('semestral_habilitado') is not None else 1
                ext_en = cfg.get('extraordinario_habilitado') if cfg.get('extraordinario_habilitado') is not None else 1

                cct_config = {
                    'captura_p1': is_period_open(p1_en, cfg.get('p1_fecha_inicio'), cfg.get('p1_fecha_fin'), has_active_special_permission),
                    'captura_p2': is_period_open(p2_en, cfg.get('p2_fecha_inicio'), cfg.get('p2_fecha_fin'), has_active_special_permission),
                    'captura_p3': is_period_open(p3_en, cfg.get('p3_fecha_inicio'), cfg.get('p3_fecha_fin'), has_active_special_permission),
                    'captura_semestral': is_period_open(sem_en, cfg.get('semestral_fecha_inicio'), cfg.get('semestral_fecha_fin'), has_active_special_permission),
                    'captura_extraordinario': is_period_open(ext_en, cfg.get('extraordinario_fecha_inicio'), cfg.get('extraordinario_fecha_fin'), has_active_special_permission),
                }

                # Si ningún periodo específico tiene fechas o habilitación explícita pero el grupo permite captura, habilitar periodos
                if not any(cct_config.values()) and (cfg.get('captura_habilitada') or cfg.get('captura_habilitada') is None):
                    cct_config = {
                        'captura_p1': True,
                        'captura_p2': True,
                        'captura_p3': True,
                        'captura_semestral': True,
                        'captura_extraordinario': True,
                    }

            # BGNE: la calificación final sigue la ventana automática (las fechas manuales solo extienden el cierre)
            if int(id_cct_grupo) == 3:
                bloqueado = bool(cfg and cfg.get('captura_habilitada') is not None and not cfg.get('captura_habilitada')
                                 and not has_active_special_permission)
                cct_config['captura_p1'] = (not bloqueado) and CalificacionesService.p1_abierto_bgne(
                    grupo, cfg, has_active_special_permission)
                # Extraordinario: solo con fechas configuradas por el admin (o prórroga), igual que al guardar
                cct_config['captura_extraordinario'] = (not bloqueado) and bool(cfg) and CalificacionesService.periodo_bti_abierto(
                    cfg, 'extraordinario', has_active_special_permission)

            # Si es docente y ningún periodo está habilitado para captura, activar solo_lectura
            if is_docente and not any(cct_config.values()):
                solo_lectura = True
                if not mensaje_restriccion:
                    mensaje_restriccion = "Captura bloqueada por la administración."

            return {
                "grupo": grupo,
                "materias": materias_horario,
                "materiaSeleccionada": materia_seleccionada,
                "idMateriaSeleccionada": int(id_materia) if id_materia else None,
                "alumnos": alumnos_califs,
                "solo_lectura": solo_lectura,
                "mensaje_restriccion": mensaje_restriccion,
                "cct_config": cct_config,
                "periodo_observaciones": periodo_obs,
                "finalizado": bool(permiso.get('finalizado')) if permiso else False,
                "periodos_enviados": periodos_enviados_resp,
                # Periodo enviado reabierto por prórroga: solo se capturan los alumnos sin calificación en él
                "periodo_solo_faltantes": periodo_solo_faltantes_resp
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _guardar_calificacion_bgne(cursor, item, id_alumno, id_materia, id_grupo, id_nivel_materia,
                                   observaciones, create_by, is_docente, allow_p1, allow_ext):
        """
        Regla BGNE (CCT 3): no hay parciales ni semestral.
          - parcial1       -> calificación ORDINARIA (se captura en la ventana p1)
          - extraordinario -> calificación del examen extraordinario (sin tope; se aprueba con 6)
          - calificacion   -> calificación EFECTIVA: la del extraordinario si existe, si no la ordinaria
        Se conservan ambas; kárdex y actas leen `calificacion`.
        """
        def num(v):
            if v is None or v == "" or str(v).strip().lower() == "null":
                return None
            return float(v)

        cursor.execute("""
            SELECT id, calificacion, parcial1, extraordinario, asistencias, total_asistencias
            FROM tb_calificaciones
            WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
        """, (id_alumno, id_materia))
        existente = cursor.fetchone()

        # Front nuevo manda la ordinaria en parcial1; el anterior la mandaba en `calificacion`
        ord_val = num(item.get("parcial1")) if "parcial1" in item else num(item.get("calificacion"))
        ext_val = num(item.get("extraordinario"))

        # Registros previos a esta regla: la ordinaria solo estaba en `calificacion`
        ord_prev = None
        ext_prev = None
        if existente:
            ext_prev = num(existente.get("extraordinario"))
            ord_prev = num(existente.get("parcial1"))
            if ord_prev is None and ext_prev is None:
                ord_prev = num(existente.get("calificacion"))

        # Un docente fuera de su ventana no puede modificar ese campo
        if is_docente:
            if not allow_p1:
                ord_val = ord_prev
            if not allow_ext:
                ext_val = ext_prev

        asist_val = item.get("asistencias") if "asistencias" in item else (existente.get("asistencias") if existente else None)
        tot_asist_val = item.get("total_asistencias") if "total_asistencias" in item else (existente.get("total_asistencias") if existente else None)

        cursor.execute("""
            DELETE FROM tb_calificaciones
            WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = 'EQUIVALENCIA'
        """, (id_alumno, id_materia))

        if ord_val is None and ext_val is None:
            if asist_val is None and tot_asist_val is None:
                cursor.execute("""
                    DELETE FROM tb_calificaciones
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                """, (id_alumno, id_materia))
                return
            calif_val = 0.0
        else:
            calif_val = float(round(ext_val if ext_val is not None else ord_val))

        tipo_acred = "EXTRAORDINARIO" if ext_val is not None else "ORDINARIO"

        if existente:
            cursor.execute("""
                UPDATE tb_calificaciones
                SET calificacion = %s, tipoAcreditacion = %s, idGrupo = %s, observaciones = %s,
                    parcial1 = %s, parcial2 = NULL, parcial3 = NULL, semestral = NULL, extraordinario = %s,
                    asistencias = %s, total_asistencias = %s,
                    id_nivel_academico = COALESCE(id_nivel_academico, %s),
                    updateBy = %s, updateAt = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (calif_val, tipo_acred, id_grupo, observaciones, ord_val, ext_val,
                  asist_val, tot_asist_val, id_nivel_materia, create_by, existente["id"]))
        else:
            cursor.execute("""
                INSERT INTO tb_calificaciones (
                    idAlumno, idMateria, idGrupo, id_nivel_academico, calificacion, tipoAcreditacion, observaciones,
                    fechaEvaluacion, createBy, parcial1, extraordinario, asistencias, total_asistencias
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s)
            """, (id_alumno, id_materia, id_grupo, id_nivel_materia, calif_val, tipo_acred, observaciones,
                  create_by, ord_val, ext_val, asist_val, tot_asist_val))

    @staticmethod
    def guardar_calificaciones_grupo_materia(id_grupo, id_materia, calificaciones, create_by="SISTEMA", id_docente=None, rol=None, finalizar=False):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Validar permiso antes de guardar si es docente
            is_docente = bool(rol and rol.upper() == 'DOCENTE')
            if is_docente and not id_docente and create_by:
                cursor.execute("""
                    SELECT idDocente FROM tb_docentes 
                    WHERE (LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) 
                           OR LOWER(TRIM(correoDocente)) = LOWER(TRIM(%s))
                           OR CONCAT(TRIM(nombreDocente), ' ', IFNULL(apPaternoDocente, ''), ' ', IFNULL(apMaternoDocente, '')) LIKE %s)
                    LIMIT 1
                """, (create_by, create_by, f"%{create_by}%"))
                found_d = cursor.fetchone()
                if found_d:
                    id_docente = found_d['idDocente'] if isinstance(found_d, dict) else found_d[0]

            if is_docente:
                perm_res = CalificacionesService.check_captura_permission(id_grupo, id_materia, id_docente, rol)
                if not perm_res['allowed']:
                    return {"error": perm_res['reason']}

            # 2. Determinar periodos habilitados si el usuario es DOCENTE
            allow_p1 = True
            allow_p2 = True
            allow_p3 = True
            allow_sem = True
            allow_ext = True
            prorroga_periodo = None   # periodo de la prórroga vigente del docente (BTI)
            solo_faltantes_bti = None  # periodo enviado reabierto por prórroga solo para alumnos sin calificación
            alumnos_ya_enviados = set()   # en ese periodo, alumnos que ya tenían calificación (no se tocan)
            perm_doc = None

            if is_docente:
                cursor.execute("""
                    SELECT p1_habilitado, p1_fecha_inicio, p1_fecha_fin,
                           p2_habilitado, p2_fecha_inicio, p2_fecha_fin,
                           p3_habilitado, p3_fecha_inicio, p3_fecha_fin,
                           semestral_habilitado, semestral_fecha_inicio, semestral_fecha_fin,
                           extraordinario_habilitado, extraordinario_fecha_inicio, extraordinario_fecha_fin,
                           captura_habilitada
                    FROM tb_grupo_periodos_captura WHERE id_grupo = %s
                """, (id_grupo,))
                cfg_grupo = cursor.fetchone()

                has_prorroga = False
                if id_docente:
                    cursor.execute("""
                        SELECT *
                        FROM tb_docente_permisos_captura
                        WHERE id_docente = %s AND id_grupo = %s AND id_materia = %s
                    """, (id_docente, id_grupo, id_materia))
                    perm_doc = cursor.fetchone()
                    if perm_doc and perm_doc.get('habilitado') and not perm_doc.get('finalizado'):
                        fl = perm_doc.get('fecha_limite')
                        hoy = date.today().strftime('%Y-%m-%d')
                        if fl and hoy <= str(fl):
                            has_prorroga = True
                    prorroga_periodo = CalificacionesService.periodo_prorroga_vigente(perm_doc)

                cursor.execute("SELECT id_centroTrabajo, fechaInicio, fechaFin FROM tb_grupos WHERE id = %s", (id_grupo,))
                g_cct = cursor.fetchone() or {}
                if int(g_cct.get('id_centroTrabajo') or 0) == 3:
                    # BGNE: la calificación final solo en la ventana automática (fechas manuales solo extienden el cierre)
                    if cfg_grupo and cfg_grupo.get('captura_habilitada') is not None and not cfg_grupo.get('captura_habilitada') and not has_prorroga:
                        return {"error": "Captura bloqueada por la administración."}
                    allow_p1 = CalificacionesService.p1_abierto_bgne(g_cct, cfg_grupo, has_prorroga)
                    allow_ext = bool(cfg_grupo) and CalificacionesService.periodo_bti_abierto(cfg_grupo, 'extraordinario', has_prorroga)
                    if not allow_p1 and not allow_ext:
                        return {"error": "Captura bloqueada por la administración."}
                elif int(g_cct.get('id_centroTrabajo') or 0) == 2:
                    # BTI: solo los periodos habilitados manualmente con fechas (o prórroga vigente)
                    if cfg_grupo and cfg_grupo.get('captura_habilitada') is not None and not cfg_grupo.get('captura_habilitada') and not has_prorroga:
                        return {"error": "Captura bloqueada por la administración."}
                    abiertos_bti = [p for p in CalificacionesService.PERIODOS_BTI
                                    if CalificacionesService.periodo_bti_abierto(cfg_grupo, p, has_prorroga, prorroga_periodo=prorroga_periodo)]
                    if not abiertos_bti:
                        return {"error": "Captura bloqueada por la administración."}
                    # Los periodos que el docente ya envió no se editan ni se reenvían;
                    # con prórroga de ese periodo solo se capturan los alumnos sin calificación
                    enviados_bti = CalificacionesService.periodos_enviados(cursor, id_docente, id_grupo, id_materia)
                    solo_faltantes_bti = CalificacionesService.periodo_solo_faltantes(perm_doc, enviados_bti) if id_docente else None
                    abiertos_bti = [p for p in abiertos_bti if p not in enviados_bti or p == solo_faltantes_bti]
                    if not abiertos_bti:
                        return {"error": "Ya enviaste las calificaciones de este periodo; no se pueden modificar ni volver a enviar."}
                    allow_p1, allow_p2, allow_p3, allow_sem, allow_ext = (
                        p in abiertos_bti for p in CalificacionesService.PERIODOS_BTI)
                elif cfg_grupo:
                    if cfg_grupo.get('captura_habilitada') is not None and not cfg_grupo.get('captura_habilitada') and not has_prorroga:
                        return {"error": "Captura bloqueada por la administración."}
                    
                    def check_period(en, st, en_date):
                        if not en:
                            return False
                        hoy = date.today().strftime('%Y-%m-%d')
                        if st and hoy < str(st):
                            return False
                        if en_date and hoy > str(en_date):
                            if not has_prorroga:
                                return False
                        return True

                    allow_p1 = check_period(cfg_grupo.get('p1_habilitado', 1), cfg_grupo.get('p1_fecha_inicio'), cfg_grupo.get('p1_fecha_fin'))
                    allow_p2 = check_period(cfg_grupo.get('p2_habilitado', 1), cfg_grupo.get('p2_fecha_inicio'), cfg_grupo.get('p2_fecha_fin'))
                    allow_p3 = check_period(cfg_grupo.get('p3_habilitado', 1), cfg_grupo.get('p3_fecha_inicio'), cfg_grupo.get('p3_fecha_fin'))
                    allow_sem = check_period(cfg_grupo.get('semestral_habilitado', 1), cfg_grupo.get('semestral_fecha_inicio'), cfg_grupo.get('semestral_fecha_fin'))
                    allow_ext = check_period(cfg_grupo.get('extraordinario_habilitado', 1), cfg_grupo.get('extraordinario_fecha_inicio'), cfg_grupo.get('extraordinario_fecha_fin'))

                    if not any([allow_p1, allow_p2, allow_p3, allow_sem, allow_ext]):
                        if cfg_grupo.get('captura_habilitada') or cfg_grupo.get('captura_habilitada') is None:
                            allow_p1 = allow_p2 = allow_p3 = allow_sem = allow_ext = True
                        else:
                            return {"error": "Captura bloqueada por la administración."}

            # 3. Validar rango de calificaciones (enteros 1 a 10) para BTI (CCT 2) y BGNE (CCT 3)
            cursor.execute("SELECT id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo_row = cursor.fetchone()
            id_cct = grupo_row.get("id_centroTrabajo") if grupo_row else None
            
            if id_cct in [2, 3]:
                for item in calificaciones:
                    # Las equivalencias se gestionan de forma especial
                    if str(item.get("tipoAcreditacion") or "").upper() == "EQUIVALENCIA":
                        continue
                    for fld in ["calificacion", "parcial1", "parcial2", "parcial3", "semestral", "extraordinario"]:
                        val = item.get(fld)
                        if val is not None and val != "" and str(val).strip().lower() != "null":
                            try:
                                f_val = float(val)
                                if f_val < 0.0 or f_val > 10.0:
                                    return {"error": f"La calificacion '{fld}' ({f_val}) debe ser un numero entero del 0 al 10."}
                            except ValueError:
                                return {"error": f"La calificacion '{fld}' no es un numero valido."}

            id_nivel_materia = None
            if id_cct == 3:
                cursor.execute("SELECT id_nivel_academico FROM tb_materias WHERE id = %s", (id_materia,))
                mat_row = cursor.fetchone()
                id_nivel_materia = mat_row.get("id_nivel_academico") if mat_row else None

            for item in calificaciones:
                id_alumno = item.get("idAlumno")
                calificacion = item.get("calificacion")
                observaciones = item.get("observaciones") or ""
                tipo_acred = (item.get("tipoAcreditacion") or "ORDINARIO").strip().upper()

                if not id_alumno:
                    continue

                # Las equivalencias las gestiona solo la administración: el docente no puede marcarlas ni quitarlas
                if is_docente:
                    cursor.execute("""
                        SELECT 1 FROM tb_calificaciones
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = 'EQUIVALENCIA' LIMIT 1
                    """, (id_alumno, id_materia))
                    ya_es_equiv = cursor.fetchone() is not None
                    if ya_es_equiv or tipo_acred == "EQUIVALENCIA":
                        continue

                if tipo_acred == "EQUIVALENCIA":
                    # Limpiar cualquier calificacion ordinaria previa para este alumno y materia
                    cursor.execute("""
                        DELETE FROM tb_calificaciones 
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                    """, (id_alumno, id_materia))

                    cursor.execute("""
                        SELECT id FROM tb_calificaciones 
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = 'EQUIVALENCIA'
                    """, (id_alumno, id_materia))
                    existente = cursor.fetchone()

                    if existente:
                        cursor.execute("""
                            UPDATE tb_calificaciones 
                            SET calificacion = 0.0, idGrupo = %s, observaciones = %s,
                                parcial1 = NULL, parcial2 = NULL, parcial3 = NULL, semestral = NULL, extraordinario = NULL,
                                updateBy = %s, updateAt = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (id_grupo, observaciones, create_by, existente["id"]))
                    else:
                        cursor.execute("""
                            INSERT INTO tb_calificaciones (
                                idAlumno, idMateria, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy
                            ) VALUES (%s, %s, %s, 0.0, 'EQUIVALENCIA', %s, CURRENT_DATE, %s)
                        """, (id_alumno, id_materia, id_grupo, observaciones, create_by))
                    continue

                if id_cct == 3:
                    CalificacionesService._guardar_calificacion_bgne(
                        cursor, item, id_alumno, id_materia, id_grupo, id_nivel_materia,
                        observaciones, create_by, is_docente, allow_p1, allow_ext
                    )
                    continue

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

                is_calif_empty = (calificacion is None or calificacion == "" or str(calificacion).strip().lower() == "null")
                all_partials_empty = all(v is None for v in [p1_val, p2_val, p3_val, sem_val, ext_val])

                # Si las calificaciones se vaciaron (null / vacio), eliminar el registro existente de tb_calificaciones únicamente si tampoco hay asistencias
                if is_calif_empty and all_partials_empty:
                    if asist_val is None and tot_asist_val is None:
                        cursor.execute("""
                            DELETE FROM tb_calificaciones 
                            WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                        """, (id_alumno, id_materia))
                        continue
                    else:
                        calif_val = 0.0

                # Al guardar ordinario, asegurarse de limpiar cualquier registro previo de equivalencia
                cursor.execute("""
                    DELETE FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = 'EQUIVALENCIA'
                """, (id_alumno, id_materia))

                if is_calif_empty:
                    # Si no viene calificacion final pero si parciales, calcular promedio
                    valid_parts = [v for v in [p1_val, p2_val, p3_val] if v is not None]
                    if ext_val is not None:
                        calif_val = float(min(round(ext_val), 7))
                    elif sem_val is not None:
                        count = 4 if len(valid_parts) == 3 else (len(valid_parts) + 1)
                        calif_val = float(round((sum(valid_parts) + sem_val) / count))
                    elif valid_parts:
                        calif_val = float(round(sum(valid_parts) / len(valid_parts)))
                    else:
                        if asist_val is None and tot_asist_val is None:
                            cursor.execute("""
                                DELETE FROM tb_calificaciones 
                                WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                            """, (id_alumno, id_materia))
                            continue
                        else:
                            calif_val = 0.0
                else:
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
                    SELECT id, parcial1, parcial2, parcial3, semestral, extraordinario
                    FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                """, (id_alumno, id_materia))
                existente = cursor.fetchone()

                if is_docente:
                    if existente:
                        if not allow_p1:
                            p1_val = float(existente["parcial1"]) if existente.get("parcial1") is not None else None
                        if not allow_p2:
                            p2_val = float(existente["parcial2"]) if existente.get("parcial2") is not None else None
                        if not allow_p3:
                            p3_val = float(existente["parcial3"]) if existente.get("parcial3") is not None else None
                        if not allow_sem:
                            sem_val = float(existente["semestral"]) if existente.get("semestral") is not None else None
                        if not allow_ext:
                            ext_val = float(existente["extraordinario"]) if existente.get("extraordinario") is not None else None
                    else:
                        if not allow_p1:
                            p1_val = None
                        if not allow_p2:
                            p2_val = None
                        if not allow_p3:
                            p3_val = None
                        if not allow_sem:
                            sem_val = None
                        if not allow_ext:
                            ext_val = None

                    # Prórroga de un periodo ya enviado: solo se capturan los alumnos sin calificación en ese periodo;
                    # las calificaciones ya enviadas se conservan tal cual (y también sus observaciones)
                    if solo_faltantes_bti and existente:
                        col = {'p1': 'parcial1', 'p2': 'parcial2', 'p3': 'parcial3',
                               'semestral': 'semestral', 'extraordinario': 'extraordinario'}[solo_faltantes_bti]
                        if existente.get(col) is not None:
                            previo = float(existente[col])
                            if solo_faltantes_bti == 'p1': p1_val = previo
                            elif solo_faltantes_bti == 'p2': p2_val = previo
                            elif solo_faltantes_bti == 'p3': p3_val = previo
                            elif solo_faltantes_bti == 'semestral': sem_val = previo
                            else: ext_val = previo
                            alumnos_ya_enviados.add(int(id_alumno))

                    # Recalcular calif_val a partir de los parciales válidos si existe algún parcial
                    if any(x is not None for x in [p1_val, p2_val, p3_val, sem_val, ext_val]):
                        if ext_val is not None:
                            calif_val = float(min(round(ext_val), 7))
                        elif sem_val is not None:
                            parts = [p for p in [p1_val, p2_val, p3_val] if p is not None]
                            count = 4 if len(parts) == 3 else (len(parts) + 1)
                            calif_val = float(round((sum(parts) + sem_val) / count))
                        else:
                            parts = [p for p in [p1_val, p2_val, p3_val] if p is not None]
                            if parts:
                                calif_val = float(round(sum(parts) / len(parts)))

                if existente:
                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, tipoAcreditacion = %s, idGrupo = %s, observaciones = %s, 
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s, 
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calif_val, tipo_acred, id_grupo, observaciones, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val, create_by, existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones (
                            idAlumno, idMateria, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy,
                            parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_alumno, id_materia, id_grupo, calif_val, tipo_acred, observaciones, create_by, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val))

            # Observaciones del parcial habilitado: la columna "Observaciones" de la captura es la de ese parcial.
            # El periodo lo decide el servidor (no el cliente). Solo filas con calificación; las equivalencias no.
            if CalificacionesService.obs_por_periodo_disponible(cursor):
                clave_obs = CalificacionesService.periodo_observaciones(
                    cursor, id_grupo, prorroga_periodo=prorroga_periodo)['clave']
                col_obs = CalificacionesService.OBS_COLUMNAS[clave_obs]   # nombre de columna de una lista fija
                for item in calificaciones:
                    if not item.get("idAlumno") or "observaciones" not in item:
                        continue
                    # Solo faltantes: las observaciones de lo ya enviado tampoco se modifican
                    if clave_obs == solo_faltantes_bti and int(item.get("idAlumno")) in alumnos_ya_enviados:
                        continue
                    cursor.execute(f"""
                        UPDATE tb_calificaciones SET {col_obs} = %s
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion != 'EQUIVALENCIA'
                    """, ((item.get("observaciones") or "").strip() or None, item.get("idAlumno"), id_materia))

            # 3. Registrar el envío
            # BTI: se bloquean solo los periodos abiertos que se enviaron (el siguiente parcial se captura cuando lo habiliten)
            if finalizar and id_docente and is_docente and id_cct == 2:
                if not CalificacionesService.envios_disponible(cursor):
                    conexion.rollback()
                    return {"error": "Falta preparar la base de datos para el envío por periodo "
                                     "(scripts/2026-11-26_envios_captura_por_periodo.sql). Avisa a la administración."}
                # Si reenvía con prórroga (solo faltantes) se actualiza la hora: así la prórroga deja de reabrirlo
                for p in abiertos_bti:
                    cursor.execute("""
                        INSERT INTO tb_docente_envios_captura (id_docente, id_grupo, id_materia, periodo)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE enviado_at = NOW()
                    """, (id_docente, id_grupo, id_materia, p))
            # BGNE y otros: se bloquea la asignatura. En BGNE la calificación final se captura en la ventana p1 (no hay semestral)
            elif finalizar and id_docente and is_docente and (allow_sem or allow_ext or (id_cct == 3 and allow_p1)):
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

    @staticmethod
    def get_asistencias_grupo_semestre(id_grupo, id_nivel_academico=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Grupo
            cursor.execute("""
                SELECT g.id, g.clave, g.id_centroTrabajo, g.id_nivel_academico, g.id_tipoPeriodo,
                       ct.nombre AS nombreCentroTrabajo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                WHERE g.id = %s
            """, (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado"}

            # Determinar id_nivel_academico activo o por defecto
            if not id_nivel_academico:
                cursor.execute("SELECT id_nivel_academico FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
                cfg = cursor.fetchone()
                if cfg and cfg.get("id_nivel_academico"):
                    id_nivel_academico = cfg["id_nivel_academico"]
                else:
                    id_nivel_academico = grupo.get("id_nivel_academico") or 7

            id_nivel_academico = int(id_nivel_academico)

            # Info de nivel académico
            cursor.execute("SELECT id, nombre, numero, tipo FROM tb_niveles_academicos WHERE id = %s", (id_nivel_academico,))
            nivel_info = cursor.fetchone() or {"id": id_nivel_academico, "nombre": f"{id_nivel_academico}º Periodo", "numero": id_nivel_academico}

            # 2. Alumnos inscritos en el grupo
            cursor.execute("""
                SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON ag.idAlumno = a.idAlumno
                WHERE ag.idGrupo = %s
                ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
            """, (id_grupo,))
            alumnos = cursor.fetchall() or []

            # 3. Asistencias guardadas en tb_calificaciones para este grupo y nivel
            cursor.execute("""
                SELECT idAlumno,
                       MAX(asistencias) as asistencias,
                       MAX(total_asistencias) as total_asistencias
                FROM tb_calificaciones
                WHERE idGrupo = %s AND (id_nivel_academico = %s OR id_nivel_academico IS NULL)
                GROUP BY idAlumno
            """, (id_grupo, id_nivel_academico))
            califs_asist = {c["idAlumno"]: c for c in (cursor.fetchall() or [])}

            # 4. Asistencias en tb_asistencias_alumnos como fallback (solo pase general)
            from app.services.asistencias_alumnos_service import AsistenciasAlumnosService as _AAS
            cursor.execute(f"""
                SELECT id_alumno,
                       COUNT(*) as total_sesiones,
                       SUM(CASE WHEN estatus IN ('A', 'R') THEN 1 ELSE 0 END) as asistencias_alumno
                FROM tb_asistencias_alumnos
                WHERE id_grupo = %s AND (id_nivel_academico = %s OR id_nivel_academico IS NULL)
                {_AAS.filtro_pase_general(cursor)}
                GROUP BY id_alumno
            """, (id_grupo, id_nivel_academico))
            rollcall_asist = {r["id_alumno"]: r for r in (cursor.fetchall() or [])}

            resultado_alumnos = []
            for al in alumnos:
                al_id = al["idAlumno"]
                saved = califs_asist.get(al_id)
                rc = rollcall_asist.get(al_id)

                asist = None
                tot = None
                if saved and (saved.get("asistencias") is not None or saved.get("total_asistencias") is not None):
                    asist = saved.get("asistencias")
                    tot = saved.get("total_asistencias")
                elif rc and rc.get("total_sesiones", 0) > 0:
                    asist = int(rc.get("asistencias_alumno") or 0)
                    tot = int(rc.get("total_sesiones") or 0)

                pct = round((asist / tot * 100), 1) if (asist is not None and tot is not None and tot > 0) else None

                resultado_alumnos.append({
                    "idAlumno": al_id,
                    "nombre": al["nombre"],
                    "apPaterno": al["apPaterno"],
                    "apMaterno": al["apMaterno"],
                    "numeroControl": al["numeroControl"],
                    "asistencias": asist,
                    "total_asistencias": tot,
                    "porcentaje": pct
                })

            return {
                "success": True,
                "grupo": grupo,
                "nivel": nivel_info,
                "id_nivel_academico": id_nivel_academico,
                "alumnos": resultado_alumnos
            }
        finally:
            cursor.close()
            conexion.close()

    # ------------------------------------------------------------------
    # Asistencias por PARCIAL (BTI): clases impartidas y asistencias de cada
    # alumno en el 1er, 2do y 3er parcial. Es lo que se imprime en la boleta.
    # El total del semestre (tb_calificaciones) se recalcula como P1 + P2 + P3.
    # ------------------------------------------------------------------
    @staticmethod
    def _asegurar_tabla_asistencias_parciales(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_asistencias_parciales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_alumno INT NOT NULL,
                id_grupo INT NOT NULL,
                id_nivel_academico INT NOT NULL,
                parcial TINYINT NOT NULL,
                total_clases INT NULL,
                asistencias INT NULL,
                updated_by VARCHAR(120) NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_alumno_grupo_nivel_parcial (id_alumno, id_grupo, id_nivel_academico, parcial),
                KEY idx_grupo_nivel (id_grupo, id_nivel_academico)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    @staticmethod
    def get_asistencias_grupo_parcial(id_grupo, id_nivel_academico, parcial):
        """Alumnos del grupo con sus clases/asistencias del parcial indicado."""
        base = CalificacionesService.get_asistencias_grupo_semestre(id_grupo, id_nivel_academico)
        if "error" in base:
            return base

        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            CalificacionesService._asegurar_tabla_asistencias_parciales(cursor)
            conexion.commit()
            id_nivel = int(base["id_nivel_academico"])
            cursor.execute("""
                SELECT id_alumno, total_clases, asistencias
                FROM tb_asistencias_parciales
                WHERE id_grupo = %s AND id_nivel_academico = %s AND parcial = %s
            """, (id_grupo, id_nivel, int(parcial)))
            guardadas = {r["id_alumno"]: r for r in (cursor.fetchall() or [])}

            alumnos = []
            for al in base["alumnos"]:
                g = guardadas.get(al["idAlumno"]) or {}
                tot = g.get("total_clases")
                asist = g.get("asistencias")
                alumnos.append({
                    "idAlumno": al["idAlumno"],
                    "nombre": al["nombre"],
                    "apPaterno": al["apPaterno"],
                    "apMaterno": al["apMaterno"],
                    "numeroControl": al["numeroControl"],
                    "total_asistencias": tot,
                    "asistencias": asist,
                    "porcentaje": round(asist / tot * 100, 1) if (asist is not None and tot) else None,
                })

            return {
                "success": True,
                "grupo": base["grupo"],
                "nivel": base["nivel"],
                "id_nivel_academico": id_nivel,
                "parcial": int(parcial),
                "alumnos": alumnos,
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_asistencias_grupo_parcial(id_grupo, id_nivel_academico, parcial, asistencias_list, create_by="SISTEMA"):
        conexion = get_connection()
        cursor = conexion.cursor()
        alumnos_ids = []
        try:
            cursor.execute("SELECT id FROM tb_grupos WHERE id = %s", (id_grupo,))
            if not cursor.fetchone():
                return {"error": "Grupo no encontrado"}

            CalificacionesService._asegurar_tabla_asistencias_parciales(cursor)
            id_nivel = int(id_nivel_academico)
            parcial = int(parcial)

            for item in asistencias_list:
                id_alumno = item.get("idAlumno")
                if not id_alumno:
                    continue
                tot = item.get("total_asistencias")
                asist = item.get("asistencias")
                tot = int(tot) if tot is not None and str(tot).strip() != "" else None
                asist = int(asist) if asist is not None and str(asist).strip() != "" else None
                alumnos_ids.append(int(id_alumno))

                if tot is None and asist is None:
                    cursor.execute("""
                        DELETE FROM tb_asistencias_parciales
                        WHERE id_alumno = %s AND id_grupo = %s AND id_nivel_academico = %s AND parcial = %s
                    """, (id_alumno, id_grupo, id_nivel, parcial))
                    continue

                cursor.execute("""
                    INSERT INTO tb_asistencias_parciales
                        (id_alumno, id_grupo, id_nivel_academico, parcial, total_clases, asistencias, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        total_clases = VALUES(total_clases),
                        asistencias = VALUES(asistencias),
                        updated_by = VALUES(updated_by)
                """, (id_alumno, id_grupo, id_nivel, parcial, tot, asist, create_by))

            # IMPORTANTE: la captura por parcial solo escribe en tb_asistencias_parciales.
            # No se toca tb_calificaciones: ahí pueden existir totales de semestre capturados antes
            # (formato anterior) y no deben sobrescribirse ni generarse renglones nuevos.
            conexion.commit()
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()

        return {"success": True, "message": "Asistencias del parcial guardadas exitosamente."}

    @staticmethod
    def get_asistencias_parciales_alumno(cursor, id_alumno):
        """{id_nivel: {parcial: {total_asistencias, asistencias}}} de todas las capturas del alumno.
        Solo lectura: si la tabla todavía no existe en el servidor, el kárdex sigue funcionando sin este dato."""
        try:
            cursor.execute("""
                SELECT id_nivel_academico, parcial, total_clases, asistencias, id_grupo, updated_at
                FROM tb_asistencias_parciales
                WHERE id_alumno = %s
                ORDER BY updated_at ASC
            """, (id_alumno,))
        except pymysql.err.ProgrammingError:
            return {}
        resultado = {}
        for r in cursor.fetchall() or []:
            # Si el alumno cambió de grupo dentro del mismo semestre, gana la captura más reciente
            resultado.setdefault(str(r["id_nivel_academico"]), {})[str(r["parcial"])] = {
                "total_asistencias": r["total_clases"],
                "asistencias": r["asistencias"],
            }
        return resultado

    @staticmethod
    def guardar_asistencias_grupo_semestre(id_grupo, id_nivel_academico, asistencias_list, create_by="SISTEMA"):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validar grupo
            cursor.execute("SELECT id, id_centroTrabajo FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado"}

            id_cct = grupo["id_centroTrabajo"]

            # Materias del nivel y CCT
            cursor.execute("""
                SELECT id FROM tb_materias
                WHERE id_nivel_academico = %s AND (idCentroTrabajo = %s OR idCentroTrabajo IS NULL)
            """, (id_nivel_academico, id_cct))
            materias = [m["id"] for m in (cursor.fetchall() or [])]

            # También incluir materias que estén asignadas al grupo en tb_horarios
            cursor.execute("SELECT DISTINCT id_materia FROM tb_horarios WHERE id_grupo = %s", (id_grupo,))
            for h in (cursor.fetchall() or []):
                if h.get("id_materia") and h["id_materia"] not in materias:
                    materias.append(h["id_materia"])

            for item in asistencias_list:
                id_alumno = item.get("idAlumno")
                if not id_alumno:
                    continue

                asist_val = int(item["asistencias"]) if (item.get("asistencias") is not None and str(item.get("asistencias")).strip() != "") else None
                tot_val = int(item["total_asistencias"]) if (item.get("total_asistencias") is not None and str(item.get("total_asistencias")).strip() != "") else None

                # Obtener IDs de materias ya existentes para este alumno en este nivel
                mat_tuple = tuple(materias) if materias else (-1,)
                cursor.execute("""
                    SELECT id, idMateria FROM tb_calificaciones
                    WHERE idAlumno = %s AND (id_nivel_academico = %s OR idGrupo = %s OR idMateria IN %s)
                """, (id_alumno, id_nivel_academico, id_grupo, mat_tuple))
                existentes = cursor.fetchall() or []
                existentes_mat_ids = {e["idMateria"] for e in existentes}

                # Actualizar los registros existentes
                if existentes:
                    cursor.execute("""
                        UPDATE tb_calificaciones
                        SET asistencias = %s,
                            total_asistencias = %s,
                            id_nivel_academico = COALESCE(id_nivel_academico, %s),
                            idGrupo = COALESCE(idGrupo, %s),
                            updateAt = NOW(),
                            updateBy = %s
                        WHERE idAlumno = %s AND (id_nivel_academico = %s OR idGrupo = %s OR idMateria IN %s)
                    """, (asist_val, tot_val, id_nivel_academico, id_grupo, create_by, id_alumno, id_nivel_academico, id_grupo, mat_tuple))

                # Insertar registros para las materias faltantes del nivel escolar
                materias_faltantes = [m_id for m_id in materias if m_id not in existentes_mat_ids]
                for id_mat in materias_faltantes:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones
                        (idAlumno, idMateria, idGrupo, id_nivel_academico, calificacion, asistencias, total_asistencias, createBy, createAt, updateBy, updateAt)
                        VALUES (%s, %s, %s, %s, 0.00, %s, %s, %s, NOW(), %s, NOW())
                    """, (id_alumno, id_mat, id_grupo, id_nivel_academico, asist_val, tot_val, create_by, create_by))

            conexion.commit()
            return {"success": True, "message": "Asistencias guardadas exitosamente."}
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()


