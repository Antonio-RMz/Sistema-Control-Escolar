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

def find_duplicates():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT id, nombreMateria, id_nivel_academico, idCentroTrabajo FROM tb_materias")
        mats = cursor.fetchall()
        print("--- DUPLICATE MATERIAS BY NORMALIZED NAME ---")
        by_name = {}
        for m in mats:
            norm = normalize_subject_name(m['nombreMateria'])
            by_name.setdefault(norm, []).append(m)
            
        for norm, list_m in by_name.items():
            if len(list_m) > 1:
                print(f"Normalized Name: {norm}")
                for m in list_m:
                    print(f"  ID: {m['id']} | Level: {m['id_nivel_academico']} | CCT: {m['idCentroTrabajo']} | Original Name: {m['nombreMateria']}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    find_duplicates()
