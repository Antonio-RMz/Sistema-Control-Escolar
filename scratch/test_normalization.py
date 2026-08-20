import unicodedata
import re
from app.config.conexion import get_connection
import pymysql

def normalize_subject_name(name):
    if not name:
        return ""
    name = name.upper().strip()
    # Replace common abbreviations/synonyms first
    name = name.replace("MET. DE LA INVESTIGACION", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACIÓN", "METODOLOGIA DE LA INVESTIGACION I")
    name = name.replace("MET. DE LA INVESTIGACION II", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("MET. DE LA INVESTIGACIÓN II", "METODOLOGIA DE LA INVESTIGACION II")
    name = name.replace("ECOLOGIA Y MED. AMBIENTE", "ECOLOGIA Y MEDIO AMBIENTE")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MEXICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    name = name.replace("ESTRUCTURA SOCIO EC. DE MÉXICO", "ESTRUCTURA SOCIOECONOMICA DE MEXICO")
    
    # Remove accents
    name = "".join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    # Remove non-alphanumeric, split and join
    name = re.sub(r'[^A-Z0-9]', ' ', name)
    name = " ".join(name.split())
    return name

BGNE_CANONICAL_MAP = {
    1: ["MATEMATICAS I", "QUIMICA I", "GEOGRAFIA", "INTRODUCCION C. SOCIALES I", "INFORMATICA I", "LECTURA Y REDACCION I", "INGLES I"],
    2: ["MATEMATICAS II", "QUIMICA II", "BIOLOGIA I", "HISTORIA DE MEXICO I", "INFORMATICA II", "LECTURA Y REDACCION II", "INGLES II"],
    3: ["MATEMATICAS III", "FISICA I", "METODOLOGIA DE LA INVESTIGACION I", "HISTORIA DE MEXICO II", "BIOLOGIA II", "LITERATURA I", "INGLES III"],
    4: ["MATEMATICAS IV", "FISICA II", "ECOLOGIA Y MEDIO AMBIENTE", "ESTRUCTURA SOCIOECONOMICA DE MEXICO", "METODOLOGIA DE LA INVESTIGACION II", "LITERATURA II", "INGLES IV"],
    5: ["INFORMATICA III", "INGLES V", "CALCULO DIFERENCIAL", "CONTABILIDAD I", "INDIVIDUO Y SOCIEDAD", "TEMAS SELECTOS DE BIOLOGIA I"],
    6: ["FILOSOFIA", "INGLES VI", "CALCULO INTEGRAL", "TEMAS SELECTOS DE BIOLOGIA II", "INFORMATICA IV", "CONTABILIDAD II"]
}

# Create a flat map of normalized canonical names to their official level
normalized_canonical = {}
for lvl, mats in BGNE_CANONICAL_MAP.items():
    for m in mats:
        normalized_canonical[normalize_subject_name(m)] = lvl

conn = get_connection()
cursor = conn.cursor(pymysql.cursors.DictCursor)

try:
    cursor.execute("""
        SELECT id, nombreMateria, id_nivel_academico, clave
        FROM tb_materias
        WHERE idCentroTrabajo = 3 OR clave LIKE 'BGNE%'
    """)
    rows = cursor.fetchall()
    print("--- MATCHING RESULTS ---")
    for r in rows:
        norm_name = normalize_subject_name(r['nombreMateria'])
        expected_level = normalized_canonical.get(norm_name)
        status = "MATCH" if expected_level == r['id_nivel_academico'] else "MISMATCH / NO MATCH"
        print(f"ID: {r['id']} | Original: {r['nombreMateria']} | Normalized: {norm_name} | Actual Level: {r['id_nivel_academico']} | Expected Level: {expected_level} | Status: {status}")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()
