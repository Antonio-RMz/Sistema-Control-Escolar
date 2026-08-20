from app.config.conexion import get_connection
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

def check_student_duplicates():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Get all grades with student name and subject details
        cursor.execute("""
            SELECT 
                c.idAlumno,
                a.nombre,
                a.apPaterno,
                c.idMateria,
                m.nombreMateria,
                m.id_nivel_academico,
                c.calificacion,
                c.tipoAcreditacion,
                COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3) as id_centroTrabajo
            FROM tb_calificaciones c
            JOIN tb_alumnos a ON c.idAlumno = a.idAlumno
            JOIN tb_materias m ON c.idMateria = m.id
            LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
            LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
        """)
        grades = cursor.fetchall()
        
        # Group by idAlumno, normalized_subject_name
        grouped = {}
        for g in grades:
            cct = g['id_centroTrabajo']
            if cct != 3: # Only BGNE
                continue
            student_id = g['idAlumno']
            student_name = f"{g['nombre']} {g['apPaterno']}"
            norm_sub = normalize_subject_name(g['nombreMateria'])
            
            key = (student_id, student_name, norm_sub)
            grouped.setdefault(key, []).append(g)
            
        print("--- STUDENTS WITH MULTIPLE GRADES FOR SAME NORMALIZED BGNE SUBJECT ---")
        count = 0
        for (student_id, student_name, norm_sub), list_g in grouped.items():
            if len(list_g) > 1:
                count += 1
                print(f"Student ID: {student_id} | Name: {student_name} | Subject: {norm_sub}")
                for g in list_g:
                    print(f"  Materia ID: {g['idMateria']} | Level: {g['id_nivel_academico']} | Grade: {g['calificacion']} | Type: {g['tipoAcreditacion']} | Original Name: {g['nombreMateria']}")
                    
        print(f"\nTotal cases found: {count}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_student_duplicates()
