from flask import Blueprint, jsonify, request
from app.services.generaciones_service import GeneracionesService

generaciones_bp = Blueprint("generaciones", __name__)


@generaciones_bp.route("/generaciones", methods=["GET"])
def get_generaciones():
    try:
        resultado = GeneracionesService.get_all()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generaciones_bp.route("/createGeneraciones", methods=["POST"])
def create_generacion():
    try:
        data = request.json
        required_fields = [
            "nombreGeneracion",
            "generacion",
            "anioInicio",
            "anioFin",
            "generacion",
            "modalidad",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        resultado = GeneracionesService.create(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
