import os
from flask import Blueprint, request, jsonify
from app.services.asistencias_service import AsistenciasService

asistencias_bp = Blueprint("asistencias", __name__)

ALLOWED_EXTENSIONS = {"xlsx", "xls"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@asistencias_bp.route("/asistencias/upload", methods=["POST"])
def upload_asistencias():
    try:
        # Verificar si el archivo está en la petición
        if "file" not in request.files:
            return jsonify({"error": "No se envió ningún archivo bajo la clave 'file'"}), 400
        
        file = request.files["file"]
        
        # Si el usuario no selecciona un archivo, el navegador puede enviar un archivo vacío sin nombre
        if file.filename == "":
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Formato de archivo no permitido. Solo se aceptan archivos Excel (.xlsx, .xls)"}), 400
        
        import datetime
        from werkzeug.utils import secure_filename
        
        # Formatear el nombre del archivo: YYYYMMDD_HHMMSS_nombre_original.xlsx
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        original_name = secure_filename(file.filename)
        if not original_name:
            original_name = "archivo_biometrico.xlsx"
            
        filename = f"{timestamp}_{original_name}"
        
        # Directorio de almacenamiento
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Procesar e importar el archivo recién guardado
        with open(file_path, "rb") as f:
            AsistenciasService.procesar_excel(f)
        
        return jsonify({
            "mensaje": "Archivo recibido y guardado correctamente",
            "filename": filename
        }), 200
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@asistencias_bp.route("/asistencias", methods=["GET"])
def get_asistencias():
    try:
        fecha_inicio = request.args.get("fecha_inicio")
        fecha_fin = request.args.get("fecha_fin")
        id_docente = request.args.get("id_docente")
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan parámetros fecha_inicio o fecha_fin"}), 400
            
        resultado = AsistenciasService.get_asistencias(fecha_inicio, fecha_fin, id_docente)
        
        import datetime
        import decimal
        for r in resultado:
            for k, v in list(r.items()):
                if isinstance(v, (datetime.timedelta, datetime.date, datetime.datetime)):
                    r[k] = str(v)
                elif isinstance(v, decimal.Decimal):
                    r[k] = float(v)
                    
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400



@asistencias_bp.route("/test_parse_direct", methods=["GET"])
def test_parse_direct():
    import glob
    import os
    try:
        # Encontrar el archivo más reciente en uploads
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads")
        files = glob.glob(os.path.join(upload_dir, "*.xlsx"))
        if not files:
            return jsonify({"error": "No se encontraron archivos en uploads"}), 404
        
        latest_file = max(files, key=os.path.getmtime)
        
        # Ejecutar una versión de prueba que retorne logs detallados
        logs = []
        logs.append(f"Archivo a procesar: {os.path.basename(latest_file)}")
        
        import pandas as pd
        import re
        import datetime
        import pymysql
        from app.config.conexion import get_connection
        
        xls = pd.ExcelFile(latest_file)
        sheet_name = None
        for name in xls.sheet_names:
            if "asistencia" in name.lower():
                sheet_name = name
                break
        if not sheet_name:
            for name in xls.sheet_names:
                if "reporte" in name.lower():
                    sheet_name = name
                    break
        if not sheet_name:
            sheet_name = xls.sheet_names[0]
            
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        period_str = None
        for r in range(min(10, len(df))):
            for c in range(len(df.columns)):
                val = str(df.iloc[r, c])
                if "Periodo:" in val:
                    dates = re.findall(r'\d{4}-\d{2}-\d{2}', val)
                    if len(dates) == 2:
                        period_str = val
                        break
                    row_vals = []
                    for next_c in range(c, min(c + 4, len(df.columns))):
                        cell_val = df.iloc[r, next_c]
                        if not pd.isna(cell_val):
                            row_vals.append(str(cell_val).strip())
                    combined_str = " ".join(row_vals)
                    dates_combined = re.findall(r'\d{4}-\d{2}-\d{2}', combined_str)
                    if len(dates_combined) == 2:
                        period_str = combined_str
                        break
                    period_str = val
                    break
            if period_str:
                break
                
        logs.append(f"Periodo detectado: {period_str}")
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', period_str)
        start_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d").date()
        
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        try:
            r = 0
            while r < len(df):
                val_col0 = str(df.iloc[r, 0]).strip()
                if "ID:" in val_col0 or val_col0 == "ID":
                    teacher_id_raw = df.iloc[r, 1]
                    try:
                        teacher_id = int(float(str(teacher_id_raw).strip()))
                    except Exception as e:
                        logs.append(f"Fila {r+1}: Error al parsear ID {teacher_id_raw}: {e}")
                        r += 1
                        continue
                        
                    logs.append(f"Docente detectado en Excel - ID: {teacher_id}")
                    
                    # 1. Obtener el nombre del docente en el Excel (Columna J / índice 9)
                    teacher_name = str(df.iloc[r, 9]).strip() if not pd.isna(df.iloc[r, 9]) else ""
                    logs.append(f"  Nombre en Excel: {teacher_name}")
                    
                    name_lower = teacher_name.lower()
                    if not (name_lower.startswith("lic") or name_lower.startswith("ing")):
                        logs.append(f"  -> Omitido: no empieza con Lic o Ing")
                        r += 2
                        continue

                    # 2. Buscar en BD
                    cursor.execute("SELECT idDocente, nombreDocente FROM tb_docentes WHERE idBiometrico = %s", (str(teacher_id),))
                    row_docente = cursor.fetchone()
                    if not row_docente:
                        logs.append(f"  -> Omitido: no se encontró idBiometrico = '{teacher_id}' en BD")
                        r += 2
                        continue
                        
                    db_teacher_id = row_docente['idDocente']
                    logs.append(f"  -> Mapeado en BD a: {row_docente['nombreDocente']} (idDocente: {db_teacher_id})")
                    
                    cursor.execute("""
                        SELECT h.diaSemana, h.horaInicio, h.horaFin, g.fechaInicio, g.fechaFin
                        FROM tb_horarios h
                        JOIN tb_grupos g ON h.id_grupo = g.id
                        WHERE h.id_docente = %s
                    """, (db_teacher_id,))
                    teacher_schedules = cursor.fetchall()
                    logs.append(f"  -> Horarios en BD: {len(teacher_schedules)}")
                    
                    r_times = r + 1
                    if r_times < len(df):
                        max_days = (end_date - start_date).days + 1
                        for col_idx in range(min(max_days, len(df.columns))):
                            cell_value = df.iloc[r_times, col_idx]
                            day_num = col_idx + 1
                            date_val = datetime.date(start_date.year, start_date.month, day_num)
                            db_weekday = date_val.weekday() + 1
                            
                            slots_dia = []
                            for s in teacher_schedules:
                                h_fecha_inicio = s['fechaInicio']
                                h_fecha_fin = s['fechaFin']
                                if isinstance(h_fecha_inicio, datetime.datetime):
                                    h_fecha_inicio = h_fecha_inicio.date()
                                if isinstance(h_fecha_fin, datetime.datetime):
                                    h_fecha_fin = h_fecha_fin.date()
                                if s['diaSemana'] == db_weekday and h_fecha_inicio <= date_val <= h_fecha_fin:
                                    slots_dia.append(s)
                                    
                            if slots_dia:
                                logs.append(f"    Fecha: {date_val} (día {db_weekday}) -> clases coincidentes: {len(slots_dia)}")
                    r += 2
                else:
                    r += 1
        finally:
            cursor.close()
            conexion.close()
            
        return jsonify({
            "logs": logs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



