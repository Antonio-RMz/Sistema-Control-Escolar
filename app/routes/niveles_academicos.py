from flask import Blueprint, jsonify
from app.services.niveles_academicos_service import NivelesAcademicosService

niveles_academicos_bp = Blueprint("niveles_academicos", __name__)


@niveles_academicos_bp.route("/getNivelAcademico", methods=["GET"])
def get_nivel_academico():
    try:
        return jsonify(NivelesAcademicosService.get_nivel_academico())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
