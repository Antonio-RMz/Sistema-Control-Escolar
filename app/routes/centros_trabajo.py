from flask import Blueprint, jsonify, request
from app.services.centros_trabajo_service import CentrosTrabajoService

centros_trabajo_bp = Blueprint("centros_trabajo", __name__)


@centros_trabajo_bp.route("/centroTrabajo", methods=["GET"])
def get_centro_trabajo():
    """
    Get centro trabajo
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
            nombre:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(CentrosTrabajoService.get_centros_trabajo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@centros_trabajo_bp.route("/centroTrabajo/<int:id_cct>", methods=["GET"])
def get_centro_trabajo_by_id(id_cct):
    """
    Get centro trabajo by id
    ---
    parameters:
      - name: id_cct
        in: path
        type: integer
        required: true
        description: Parámetro id_cct
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
            nombre:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        cct = CentrosTrabajoService.get_by_id(id_cct)
        if not cct:
            return jsonify({"error": "Centro de trabajo no encontrado"}), 404
        return jsonify(cct)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@centros_trabajo_bp.route("/createCentroTrabajo", methods=["POST"])
def create_centro_trabajo():
    """
    Create centro trabajo
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
            nombre:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if not data.get("clave") or not data.get("nombre"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CentrosTrabajoService.create_centro_trabajo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
