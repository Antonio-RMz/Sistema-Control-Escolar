from flask import Blueprint, jsonify, request
from app.services.metricas_service import MetricasService

metricas_bp = Blueprint("metricas", __name__)


@metricas_bp.route("/metricas", methods=["GET"])
def get_metricas():
    """
    Métricas del plantel (fase 1: resumen, asistencia y alumnos en riesgo)
    ---
    tags:
      - Metricas
    parameters:
      - name: id_centro_trabajo
        in: query
        type: integer
        description: 2 = BTI, 3 = BGNE
      - name: id_grupo
        in: query
        type: integer
      - name: periodo
        in: query
        type: string
        description: actual | 4s | 12s | personalizado
      - name: desde
        in: query
        type: string
      - name: hasta
        in: query
        type: string
    responses:
      200:
        description: Métricas del plantel
    """
    try:
        resultado = MetricasService.get_metricas(
            request.args.get("id_centro_trabajo", 2),
            request.args.get("id_grupo") or None,
            request.args.get("periodo") or "actual",
            request.args.get("desde") or None,
            request.args.get("hasta") or None,
        )
        if isinstance(resultado, tuple):
            return jsonify(resultado[0]), resultado[1]
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
