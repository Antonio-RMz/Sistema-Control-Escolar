from flask import Blueprint, jsonify, request
from app.services.cursos_extra_service import CursosExtraService

cursos_extra_bp = Blueprint("cursos_extra", __name__)


@cursos_extra_bp.route("/createCursoExtra", methods=["POST"])
def create_curso_extracurricular():
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
    try:
        return jsonify(CursosExtraService.get_cursos_extracurriculares())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
