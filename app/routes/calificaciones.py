from flask import Blueprint, jsonify, request
from app.services.calificaciones_service import CalificacionesService

calificaciones_bp = Blueprint("calificaciones", __name__)

@calificaciones_bp.route("/alumnos/<int:idAlumno>/kardex", methods=["GET"])
@calificaciones_bp.route("/calificaciones/kardex/<int:idAlumno>", methods=["GET"])
def get_kardex(idAlumno):
    try:
        resultado = CalificacionesService.get_kardex_alumno(idAlumno)
        if "error" in resultado:
            return jsonify(resultado), 404 if resultado["error"] == "Alumno no encontrado" else 500
        return jsonify({"success": True, "data": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calificaciones_bp.route("/alumnos/<int:idAlumno>/calificaciones", methods=["POST"])
@calificaciones_bp.route("/calificaciones/alumno/<int:idAlumno>", methods=["POST"])
def save_calificaciones(idAlumno):
    try:
        data = request.json or {}
        calificaciones = data.get("calificaciones") or (data if isinstance(data, list) else [])
        user = data.get("user", "SISTEMA") if isinstance(data, dict) else "SISTEMA"

        resultado = CalificacionesService.guardar_calificaciones_alumno(idAlumno, calificaciones, user)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calificaciones_bp.route("/grupos/<int:idGrupo>/calificaciones-materia", methods=["GET"])
def get_calificaciones_grupo_materia(idGrupo):
    try:
        id_materia = request.args.get("id_materia")
        resultado = CalificacionesService.get_calificaciones_grupo_materia(idGrupo, id_materia)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify({"success": True, "data": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calificaciones_bp.route("/grupos/<int:idGrupo>/calificaciones-materia/<int:idMateria>", methods=["POST"])
def save_calificaciones_grupo_materia(idGrupo, idMateria):
    try:
        data = request.json or {}
        calificaciones = data.get("calificaciones") or (data if isinstance(data, list) else [])
        user = data.get("user", "SISTEMA") if isinstance(data, dict) else "SISTEMA"

        resultado = CalificacionesService.guardar_calificaciones_grupo_materia(idGrupo, idMateria, calificaciones, user)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
