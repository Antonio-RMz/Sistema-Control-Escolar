from flask import Blueprint, jsonify, request
from app.services.materias_service import MateriasService

materias_bp = Blueprint("materias", __name__)


@materias_bp.route("/materias", methods=["GET"])
def get_materias():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))
        search = request.args.get("search", "").strip()
        id_materia = request.args.get("id_materia")

        resultado = MateriasService.get_materias(page, limit, search, id_materia)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@materias_bp.route("/createMateria", methods=["POST"])
def create_materia():
    try:
        data = request.json

        if not data.get("nombreMateria") or not data.get("estatusMateria"):
            return jsonify({"error": "Faltan datos"}), 400

        # Validar que docentes sea lista si viene
        if "docentes" in data and not isinstance(data.get("docentes"), list):
            return jsonify({"error": "docentes debe ser una lista"}), 400

        return jsonify(MateriasService.create_materia(data))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@materias_bp.route("/deleteMateria/<int:id_materia>", methods=["DELETE"])
def delete_materia(id_materia):
    try:
        return jsonify(MateriasService.delete_materia(id_materia))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@materias_bp.route("/updateMateria/<int:id_materia>", methods=["PUT"])
def update_materia(id_materia):
    try:
        data = request.json

        if not data.get("nombreMateria") or not data.get("estatusMateria"):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        # Validar que docentes sea una lista si está presente
        if "docentes" in data and not isinstance(data.get("docentes"), list):
            return jsonify({"error": "docentes debe ser una lista"}), 400

        return jsonify(MateriasService.update_materia(id_materia, data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
