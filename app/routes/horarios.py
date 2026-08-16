from flask import Blueprint, jsonify, request
from app.services.horarios_service import HorariosService

horarios_bp = Blueprint("horarios", __name__)


@horarios_bp.route("/createHorarioGrupo", methods=["POST"])
def create_horario_grupo():
    try:
        data = request.json
        hora_inicio = data.get("horaInicio") or data.get("horainicio")
        hora_fin = data.get("horaFin") or data.get("horafin")
        if not data.get("id_grupo") or (not data.get("id_materia") and not data.get("materias")) or not data.get("id_docente") or not data.get("diaSemana") or not hora_inicio or not hora_fin or not data.get("aula"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(HorariosService.create_horario_grupo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/validacionHorario", methods=["POST"])
def validacionHorario():
    try:
        data = request.json
        if not data.get("id_grupo") or not data.get("id_materia") or not data.get("id_docente") or not data.get("diaSemana") or not data.get("horaInicio") or not data.get("horaFin"):
            return jsonify({"error": "Faltan datos"}), 400
        es_prehorario = data.get("es_prehorario", 0)
        return jsonify(HorariosService.validacionHorario(
            data.get("id_grupo"),
            data.get("id_materia"),
            data.get("id_docente"),
            data.get("diaSemana"),
            data.get("horaInicio"),
            data.get("horaFin"),
            es_prehorario
        ))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/getHorariosGrupo/<int:id_grupo>", methods=["GET"])
def getHorariosGrupo(id_grupo):
    try:
        agrupado = request.args.get("agrupado", "false").lower() == "true"
        es_prehorario = int(request.args.get("es_prehorario", "0"))
        return jsonify(HorariosService.getHorariosGrupo(id_grupo, agrupado, es_prehorario))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/deleteHorarioGrupo/<int:id_horario>", methods=["DELETE"])
def delete_horario_grupo(id_horario):
    try:
        return jsonify(HorariosService.deleteHorarioGrupo(id_horario))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/getHorariosDocente/<int:id_docente>", methods=["GET"])
def get_horarios_docente(id_docente):
    try:
        return jsonify(HorariosService.getHorariosDocente(id_docente))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

