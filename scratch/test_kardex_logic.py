import unicodedata
import re
from app.config.conexion import get_connection
import pymysql

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

def test_kardex_logic(id_alumno):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 1. Obtener datos generales del alumno
        cursor.execute("""
            SELECT 
                a.idAlumno,
                a.nombre,
                COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3) AS idCentroTrabajo
            FROM tb_alumnos a
            LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
            LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
            WHERE a.idAlumno = %s
        """, (id_alumno,))
        alumno = cursor.fetchone()
        if not alumno:
            print("Student not found")
            return
        
        id_cct = alumno["idCentroTrabajo"] or 3
        print(f"Student: {alumno['nombre']} | CCT: {id_cct}")

        # 2. Obtener niveles
        cursor.execute("""
            SELECT n.id AS idNivel, n.nombre AS nombreNivel, n.numero AS numeroNivel, n.tipo AS tipoPeriodo
            FROM tb_niveles_academicos n
            JOIN tb_tipoperiodo tp ON n.id_tipoPeriodo = tp.id
            JOIN tb_centrotrabajo ct ON ct.idTipoPeriodo = tp.id
            WHERE ct.id = %s AND n.activo = 1
            ORDER BY n.numero ASC
        """, (id_cct,))
        niveles = cursor.fetchall()

        # 3. Obtener todas las materias del CCT
        cursor.execute("""
            SELECT m.id AS idMateria, m.nombreMateria, m.clave AS claveMateria, m.id_nivel_academico, m.orden
            FROM tb_materias m
            WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
        """, (id_cct,))
        todas_materias = cursor.fetchall()

        # 4. Obtener todas las calificaciones del alumno
        cursor.execute("""
            SELECT 
                c.id AS idCalificacion, c.idMateria, c.calificacion, c.tipoAcreditacion,
                c.observaciones, c.fechaEvaluacion, c.idGrupo,
                c.parcial1, c.parcial2, c.parcial3, c.semestral, c.extraordinario,
                c.asistencias, c.total_asistencias,
                m.nombreMateria, m.id_nivel_academico AS level_materia
            FROM tb_calificaciones c
            JOIN tb_materias m ON c.idMateria = m.id
            WHERE c.idAlumno = %s
        """, (id_alumno,))
        calificaciones = list(cursor.fetchall())

        # Inject mock duplicate grade for testing the merge logic
        # Student gets a grade for ID 105: "GEOGRAFÍA", level 5, which should merge into canonical ID 9 (level 1)
        calificaciones.append({
            "idCalificacion": 999,
            "idMateria": 105,
            "calificacion": 9.5,
            "tipoAcreditacion": "ORDINARIO",
            "observaciones": "Mock duplicate grade",
            "fechaEvaluacion": "2026-08-20",
            "idGrupo": 1,
            "parcial1": 9.0,
            "parcial2": 10.0,
            "parcial3": 9.5,
            "semestral": 9.5,
            "extraordinario": None,
            "asistencias": 10,
            "total_asistencias": 10,
            "nombreMateria": "GEOGRAFÍA",
            "level_materia": 5
        })

        # 5. Mapear calificaciones por nombre normalizado (para BGNE)
        is_bgne = (id_cct == 3)
        califs_mapped = {}
        for calif in calificaciones:
            if is_bgne:
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
            else:
                califs_mapped[calif["idMateria"]] = calif

        # 6. Filtrar materias a mostrar en base a canonical levels
        materias_filtradas = []
        for mat in todas_materias:
            m_id = mat["idMateria"]
            m_name = mat["nombreMateria"]
            m_level = mat["id_nivel_academico"]
            
            if is_bgne:
                norm_name = normalize_subject_name(m_name)
                if norm_name in BGNE_NORMALIZED_CANONICAL:
                    canonical_level = BGNE_NORMALIZED_CANONICAL[norm_name]
                    if m_level == canonical_level:
                        mat["id_nivel_academico"] = canonical_level
                        materias_filtradas.append(mat)
                    else:
                        # Duplicate/Non-canonical record
                        continue
                else:
                    # Non-canonical subject, keep under current level
                    materias_filtradas.append(mat)
            else:
                materias_filtradas.append(mat)

        # 7. Combinar materias y calificaciones
        materias_califs = []
        for mat in materias_filtradas:
            m_id = mat["idMateria"]
            m_name = mat["nombreMateria"]
            
            if is_bgne:
                norm_name = normalize_subject_name(m_name)
                calif = califs_mapped.get(norm_name)
            else:
                calif = califs_mapped.get(m_id)
                
            row = {
                "idMateria": m_id,
                "nombreMateria": m_name,
                "claveMateria": mat["claveMateria"],
                "id_nivel_academico": mat["id_nivel_academico"],
                "orden": mat.get("orden"),
                "idCalificacion": calif["idCalificacion"] if calif else None,
                "calificacion": float(calif["calificacion"]) if calif and calif["calificacion"] is not None else None,
                "tipoAcreditacion": calif["tipoAcreditacion"] if calif else None,
            }
            materias_califs.append(row)

        materias_califs.sort(key=lambda x: (x["id_nivel_academico"] or 99, x.get("orden") if x.get("orden") is not None else 9999, x["idMateria"]))

        # 8. Agrupar por nivel y mostrar
        for nivel in niveles:
            id_nivel = nivel["idNivel"]
            mats_nivel = [m for m in materias_califs if m.get("id_nivel_academico") == id_nivel]
            print(f"\n--- {nivel['nombreNivel']} (Total materias: {len(mats_nivel)}) ---")
            for m in mats_nivel:
                print(f"Subject: {m['nombreMateria']} (ID: {m['idMateria']}, Level: {m['id_nivel_academico']}) | Grade: {m['calificacion']} | Acreditación: {m['tipoAcreditacion']}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_kardex_logic(6)
