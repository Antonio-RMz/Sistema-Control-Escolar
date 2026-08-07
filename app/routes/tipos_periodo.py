from flask import Blueprint, jsonify, request
from app.services.tipos_periodo_service import TiposPeriodoService

tipos_periodo_bp = Blueprint("tipos_periodo", __name__)


@tipos_periodo_bp.route("/tipoPeriodo", methods=["GET"])
def get_tipo_periodo():
    try:
        return jsonify(TiposPeriodoService.get_tipos_periodo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tipos_periodo_bp.route("/createTipoPeriodo", methods=["POST"])
def create_tipo_periodo():
    try:
        data = request.json
        if not data.get("nombrePeriodo") or not data.get("descripcionPeriodo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(TiposPeriodoService.create_tipo_periodo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
