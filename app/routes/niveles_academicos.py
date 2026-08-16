from flask import Blueprint, jsonify, request
from app.services.niveles_academicos_service import NivelesAcademicosService

niveles_academicos_bp = Blueprint("niveles_academicos", __name__)


@niveles_academicos_bp.route("/getNivelAcademico", methods=["GET"])
def get_nivel_academico():
    """
    Get nivel academico
    ---
    parameters:
      - name: idCentroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro idCentroTrabajo
      - name: id_centroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centroTrabajo
      - name: idTipoPeriodo
        in: query
        type: string
        required: false
        description: Parámetro idTipoPeriodo
      - name: id_tipoPeriodo
        in: query
        type: string
        required: false
        description: Parámetro id_tipoPeriodo
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo")
        id_tipo_periodo = request.args.get("idTipoPeriodo") or request.args.get("id_tipoPeriodo")
        resultado = NivelesAcademicosService.get_nivel_academico(id_centro_trabajo, id_tipo_periodo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
