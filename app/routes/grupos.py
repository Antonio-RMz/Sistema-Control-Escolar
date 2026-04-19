from flask import Blueprint, jsonify, request
from app.services.grupos_service import GruposService

grupos_bp = Blueprint("grupos", __name__)


@grupos_bp.route("/grupos", methods=["GET"])
def get_grupos():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '').strip()
        
        resultado = GruposService.get_all(page, limit, search)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@grupos_bp.route("/grupos", methods=["POST"])
def create_grupo():
    try:
        data = request.json
        if not data.get("clave") or not data.get("fechaCreacion"):
            return jsonify({"error": "Faltan datos"}), 400

        resultado = GruposService.create(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
