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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@asistencias_bp.route("/clear_asistencias", methods=["DELETE"])
def clear_asistencias():
    from app.config.conexion import get_connection
    import pymysql
    conexion = get_connection()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM tb_asistencias_docentes")
        conexion.commit()
        return jsonify({"success": True, "message": "Datos de asistencia limpiados correctamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()


@asistencias_bp.route("/asistencias/alumnos/grupo/<int:id_grupo>", methods=["GET"])
def get_asistencias_alumnos_grupo(id_grupo):
    try:
        id_materia = request.args.get("id_materia", type=int)
        id_docente = request.args.get("id_docente", type=int)
        from app.services.asistencias_alumnos_service import AsistenciasAlumnosService
        resultado = AsistenciasAlumnosService.get_asistencias_grupo(id_grupo, id_materia, id_docente)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@asistencias_bp.route("/asistencias/alumnos/guardar", methods=["POST"])
def guardar_asistencias_alumnos():
    try:
        data = request.json
        id_grupo = data.get("id_grupo")
        id_materia = int(data.get("id_materia")) if data.get("id_materia") is not None else None
        id_docente = int(data.get("id_docente")) if data.get("id_docente") is not None else None
        asistencias_list = data.get("asistencias", [])
        
        if not id_grupo:
            return jsonify({"error": "Falta el parámetro id_grupo"}), 400
            
        from app.services.asistencias_alumnos_service import AsistenciasAlumnosService
        resultado = AsistenciasAlumnosService.guardar_asistencias(id_grupo, asistencias_list, id_materia, id_docente)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@asistencias_bp.route("/asistencias/alumnos/justificar", methods=["POST"])
def justificar_falta_alumno():
    try:
        data = request.json
        id_alumno = data.get("id_alumno")
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")
        motivo = data.get("motivo")
        
        if not id_alumno or not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan parámetros requeridos (id_alumno, fecha_inicio, fecha_fin)"}), 400
            
        from app.services.justificaciones_service import JustificacionesService
        resultado = JustificacionesService.crear_justificacion(id_alumno, fecha_inicio, fecha_fin, motivo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@asistencias_bp.route("/asistencias/alumnos/hoy", methods=["GET"])
def get_asistencias_hoy():
    from app.config.conexion import get_connection
    import datetime
    conexion = get_connection()
    cursor = conexion.cursor()
    try:
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT DISTINCT id_grupo FROM tb_asistencias_alumnos WHERE fecha = %s", (hoy,))
        rows = cursor.fetchall()
        grupo_ids = [r['id_grupo'] for r in rows if r.get('id_grupo') is not None]
        return jsonify(grupo_ids)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()




