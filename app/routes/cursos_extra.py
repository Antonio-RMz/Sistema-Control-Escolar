from flask import Blueprint, jsonify, request
from app.services.cursos_extra_service import CursosExtraService

cursos_extra_bp = Blueprint("cursos_extra", __name__)


@cursos_extra_bp.route("/createCursoExtra", methods=["POST"])
def create_curso_extracurricular():
    """
    Create curso extracurricular
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            idCentroTrabajo:
              type: string
            idDocente:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if (
            not data.get("nombre")
            or not data.get("idCentroTrabajo")
            or not data.get("idDocente")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CursosExtraService.create_curso_extracurricular(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cursos_extra_bp.route("/getCursosExtra", methods=["GET"])
def get_cursos_extracurriculares():
    """
    Get cursos extracurriculares
    ---
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(CursosExtraService.get_cursos_extracurriculares())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
