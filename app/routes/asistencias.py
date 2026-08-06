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




