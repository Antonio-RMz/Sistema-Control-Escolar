from flask import Blueprint, jsonify, request
from app.services.calificaciones_service import CalificacionesService

calificaciones_bp = Blueprint("calificaciones", __name__)

@calificaciones_bp.route("/alumnos/<int:idAlumno>/kardex", methods=["GET"])
@calificaciones_bp.route("/calificaciones/kardex/<int:idAlumno>", methods=["GET"])
def get_kardex(idAlumno):
    """
    Get kardex
    ---
    parameters:
      - name: idAlumno
        in: path
        type: integer
        required: true
        description: Parámetro idAlumno
      - name: id_materia
        in: query
        type: string
        required: false
        description: Parámetro id_materia
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            calificaciones:
              type: string
            user:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
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
    """
    Save calificaciones
    ---
    parameters:
      - name: idAlumno
        in: path
        type: integer
        required: true
        description: Parámetro idAlumno
      - name: id_materia
        in: query
        type: string
        required: false
        description: Parámetro id_materia
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            calificaciones:
              type: string
            user:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
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
    """
    Get calificaciones grupo materia
    ---
    parameters:
      - name: idGrupo
        in: path
        type: integer
        required: true
        description: Parámetro idGrupo
      - name: id_materia
        in: query
        type: string
        required: false
        description: Parámetro id_materia
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            calificaciones:
              type: string
            user:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        id_materia = request.args.get("id_materia")
        id_docente = request.args.get("id_docente")
        rol = request.args.get("rol")
        resultado = CalificacionesService.get_calificaciones_grupo_materia(idGrupo, id_materia, id_docente, rol)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify({"success": True, "data": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calificaciones_bp.route("/grupos/<int:idGrupo>/calificaciones-materia/<int:idMateria>", methods=["POST"])
def save_calificaciones_grupo_materia(idGrupo, idMateria):
    """
    Save calificaciones grupo materia
    ---
    parameters:
      - name: idGrupo
        in: path
        type: integer
        required: true
        description: Parámetro idGrupo
      - name: idMateria
        in: path
        type: integer
        required: true
        description: Parámetro idMateria
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            calificaciones:
              type: string
            user:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
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


@calificaciones_bp.route("/grupos/<int:idGrupo>/check-captura-permission/<int:idMateria>", methods=["GET"])
def check_captura_permission(idGrupo, idMateria):
    try:
        id_docente = request.args.get("id_docente")
        rol = request.args.get("rol")
        resultado = CalificacionesService.check_captura_permission(idGrupo, idMateria, id_docente, rol)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e), "allowed": False}), 500
