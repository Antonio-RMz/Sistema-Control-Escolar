from flask import Blueprint, jsonify, request
from app.services.tipos_periodo_service import TiposPeriodoService

tipos_periodo_bp = Blueprint("tipos_periodo", __name__)


@tipos_periodo_bp.route("/tipoPeriodo", methods=["GET"])
def get_tipo_periodo():
    """
    Obtener lista de tipos de periodo
    ---
    responses:
      200:
        description: Retorna un listado de todos los tipos de periodo registrados.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombrePeriodo:
                type: string
              descripcionPeriodo:
                type: string
      500:
        description: Error al obtener los tipos de periodo.
    """
    try:
        return jsonify(TiposPeriodoService.get_tipos_periodo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tipos_periodo_bp.route("/createTipoPeriodo", methods=["POST"])
def create_tipo_periodo():
    """
    Crear un nuevo tipo de periodo
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombrePeriodo
            - descripcionPeriodo
          properties:
            nombrePeriodo:
              type: string
              example: SEMESTRAL
            descripcionPeriodo:
              type: string
              example: Periodo que abarca seis meses de clases.
    responses:
      200:
        description: Tipo de periodo creado exitosamente.
        schema:
          type: object
      400:
        description: Datos inválidos o faltantes.
      500:
        description: Error interno del servidor.
    """
    try:
        data = request.json
        if not data.get("nombrePeriodo") or not data.get("descripcionPeriodo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(TiposPeriodoService.create_tipo_periodo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
