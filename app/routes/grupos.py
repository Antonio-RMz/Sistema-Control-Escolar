from flask import Blueprint, jsonify, request
from app.services.grupos_service import GruposService

grupos_bp = Blueprint("grupos", __name__)


@grupos_bp.route("/grupos", methods=["GET"])
def get_grupos():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)
        search = request.args.get("search", "").strip()
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo")
        id_nivel_academico = request.args.get("idNivelAcademico") or request.args.get("id_nivel_academico")
        id_generacion = request.args.get("idGeneracion") or request.args.get("id_generacion")
        status_grupo = request.args.get("statusGrupo") or request.args.get("status")
        modalidad_horario = request.args.get("modalidadHorario") or request.args.get("jornada")
        dia = request.args.get("dia") or request.args.get("diaClase")

        resultado = GruposService.get_all(
            page=page,
            limit=limit,
            search=search,
            id_centro_trabajo=id_centro_trabajo,
            id_nivel_academico=id_nivel_academico,
            id_generacion=id_generacion,
            status_grupo=status_grupo,
            modalidad_horario=modalidad_horario,
            dia=dia,
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@grupos_bp.route("/createGrupos", methods=["POST"])
def create_grupo():
    try:
        data = request.json
        if not data.get("clave") or not data.get("fechaCreacion"):
            return jsonify({"error": "Faltan datos"}), 400

        resultado = GruposService.create(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@grupos_bp.route("/updateGrupo/<int:id_grupo>", methods=["PUT"])
def update_grupo(id_grupo):
    try:
        data = request.json
        if not data.get("clave") or not data.get("fechaCreacion"):
            return jsonify({"error": "Faltan datos"}), 400
        resultado = GruposService.update(id_grupo, data)
        return jsonify(resultado)   
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@grupos_bp.route("/getGrupo/<int:id_grupo>", methods=["GET"])
def get_grupo(id_grupo):
    try:
        resultado = GruposService.get_grupo(id_grupo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500