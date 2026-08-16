from flask import Blueprint, jsonify, request
from app.services.planes_estudio_service import PlanesEstudioService

planes_estudio_bp = Blueprint("planes_estudio", __name__)


@planes_estudio_bp.route("/createPlanEstudios", methods=["POST"])
def create_plan_estudios():
    """
    Create plan estudios
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombrePlan:
              type: string
            descripcionPlan:
              type: string
            estatusPlan:
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
            not data.get("nombrePlan")
            or not data.get("descripcionPlan")
            or not data.get("estatusPlan")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(PlanesEstudioService.create_plan_estudios(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planes_estudio_bp.route("/getPlanesEstudio", methods=["GET"])
def get_planes_estudio():
    """
    Get planes estudio
    ---
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(PlanesEstudioService.get_planes_estudio())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
