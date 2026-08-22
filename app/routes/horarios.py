from flask import Blueprint, jsonify, request
from app.services.horarios_service import HorariosService

horarios_bp = Blueprint("horarios", __name__)


@horarios_bp.route("/createHorarioGrupo", methods=["POST"])
def create_horario_grupo():
    """
    Create horario grupo
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            horaInicio:
              type: string
            horainicio:
              type: string
            horaFin:
              type: string
            horafin:
              type: string
            id_grupo:
              type: string
            id_materia:
              type: string
            materias:
              type: string
            id_docente:
              type: string
            diaSemana:
              type: string
            aula:
              type: string
            es_prehorario:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
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
    """
    Validacionhorario
    ---
    parameters:
      - name: agrupado
        in: query
        type: string
        required: false
        description: Parámetro agrupado
      - name: es_prehorario
        in: query
        type: string
        required: false
        description: Parámetro es_prehorario
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            id_grupo:
              type: string
            id_materia:
              type: string
            id_docente:
              type: string
            diaSemana:
              type: string
            horaInicio:
              type: string
            horaFin:
              type: string
            es_prehorario:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if not data.get("id_grupo") or not data.get("id_materia") or not data.get("id_docente") or not data.get("diaSemana") or not data.get("horaInicio") or not data.get("horaFin"):
            return jsonify({"error": "Faltan datos"}), 400
        es_prehorario = data.get("es_prehorario", 0)
        aula = data.get("aula")
        exclude_ids = data.get("exclude_ids")
        return jsonify(HorariosService.validacionHorario(
            data.get("id_grupo"),
            data.get("id_materia"),
            data.get("id_docente"),
            data.get("diaSemana"),
            data.get("horaInicio"),
            data.get("horaFin"),
            es_prehorario,
            aula,
            exclude_ids
        ))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/getHorariosGrupo/<int:id_grupo>", methods=["GET"])
def getHorariosGrupo(id_grupo):
    """
    Gethorariosgrupo
    ---
    parameters:
      - name: id_grupo
        in: path
        type: integer
        required: true
        description: Parámetro id_grupo
      - name: agrupado
        in: query
        type: string
        required: false
        description: Parámetro agrupado
      - name: es_prehorario
        in: query
        type: string
        required: false
        description: Parámetro es_prehorario
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        agrupado = request.args.get("agrupado", "false").lower() == "true"
        es_prehorario = int(request.args.get("es_prehorario", "0"))
        return jsonify(HorariosService.getHorariosGrupo(id_grupo, agrupado, es_prehorario))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/deleteHorarioGrupo/<int:id_horario>", methods=["DELETE"])
def delete_horario_grupo(id_horario):
    """
    Delete horario grupo
    ---
    parameters:
      - name: id_horario
        in: path
        type: integer
        required: true
        description: Parámetro id_horario
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(HorariosService.deleteHorarioGrupo(id_horario))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@horarios_bp.route("/getHorariosDocente/<int:id_docente>", methods=["GET"])
def get_horarios_docente(id_docente):
    """
    Get horarios docente
    ---
    parameters:
      - name: id_docente
        in: path
        type: integer
        required: true
        description: Parámetro id_docente
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(HorariosService.getHorariosDocente(id_docente))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

