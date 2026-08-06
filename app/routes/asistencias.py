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
        
        # Procesar el archivo en memoria directamente
        registros_procesados = AsistenciasService.procesar_excel(file.stream)
        
        return jsonify({
            "mensaje": "Asistencias procesadas y guardadas correctamente",
            "registros_procesados": registros_procesados
        }), 200
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
