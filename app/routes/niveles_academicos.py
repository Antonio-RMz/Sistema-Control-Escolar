from flask import Blueprint, jsonify, request
from app.services.niveles_academicos_service import NivelesAcademicosService

niveles_academicos_bp = Blueprint("niveles_academicos", __name__)


@niveles_academicos_bp.route("/getNivelAcademico", methods=["GET"])
def get_nivel_academico():
    try:
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo")
        id_tipo_periodo = request.args.get("idTipoPeriodo") or request.args.get("id_tipoPeriodo")
        resultado = NivelesAcademicosService.get_nivel_academico(id_centro_trabajo, id_tipo_periodo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
