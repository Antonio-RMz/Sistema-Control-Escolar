from flask import Blueprint, jsonify, request
from app.services.grupos_service import GruposService

grupos_bp = Blueprint("grupos", __name__)


@grupos_bp.route("/grupos", methods=["GET"])
def get_grupos():
    """
    Get grupos
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: Parámetro page
      - name: limit
        in: query
        type: string
        required: false
        description: Parámetro limit
      - name: search
        in: query
        type: string
        required: false
        description: Parámetro search
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
      - name: id_centro_trabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centro_trabajo
      - name: idNivelAcademico
        in: query
        type: string
        required: false
        description: Parámetro idNivelAcademico
      - name: id_nivel_academico
        in: query
        type: string
        required: false
        description: Parámetro id_nivel_academico
      - name: idGeneracion
        in: query
        type: string
        required: false
        description: Parámetro idGeneracion
      - name: id_generacion
        in: query
        type: string
        required: false
        description: Parámetro id_generacion
      - name: statusGrupo
        in: query
        type: string
        required: false
        description: Parámetro statusGrupo
      - name: status
        in: query
        type: string
        required: false
        description: Parámetro status
      - name: status_grupo
        in: query
        type: string
        required: false
        description: Parámetro status_grupo
      - name: modalidadHorario
        in: query
        type: string
        required: false
        description: Parámetro modalidadHorario
      - name: jornada
        in: query
        type: string
        required: false
        description: Parámetro jornada
      - name: modalidad_horario
        in: query
        type: string
        required: false
        description: Parámetro modalidad_horario
      - name: dia
        in: query
        type: string
        required: false
        description: Parámetro dia
      - name: diaClase
        in: query
        type: string
        required: false
        description: Parámetro diaClase
      - name: dia_clase
        in: query
        type: string
        required: false
        description: Parámetro dia_clase
      - name: idDocente
        in: query
        type: string
        required: false
        description: Parámetro idDocente
      - name: id_docente
        in: query
        type: string
        required: false
        description: Parámetro id_docente
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
            fechaCreacion:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)
        search = request.args.get("search", "").strip()
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo") or request.args.get("id_centro_trabajo")
        id_nivel_academico = request.args.get("idNivelAcademico") or request.args.get("id_nivel_academico") or request.args.get("id_nivel_academico")
        id_generacion = request.args.get("idGeneracion") or request.args.get("id_generacion")
        status_grupo = request.args.get("statusGrupo") or request.args.get("status") or request.args.get("status_grupo")
        modalidad_horario = request.args.get("modalidadHorario") or request.args.get("jornada") or request.args.get("modalidad_horario")
        dia = request.args.get("dia") or request.args.get("diaClase") or request.args.get("dia_clase")
        id_docente = request.args.get("idDocente") or request.args.get("id_docente")

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
            id_docente=id_docente
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@grupos_bp.route("/createGrupos", methods=["POST"])
def create_grupo():
    """
    Create grupo
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
            fechaCreacion:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if not data.get("clave") or not data.get("fechaCreacion"):
            return jsonify({"error": "Faltan datos"}), 400

        resultado = GruposService.create(data)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@grupos_bp.route("/updateGrupo/<int:id_grupo>", methods=["PUT"])
def update_grupo(id_grupo):
    """
    Update grupo
    ---
    parameters:
      - name: id_grupo
        in: path
        type: integer
        required: true
        description: Parámetro id_grupo
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
            fechaCreacion:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if not data.get("clave") or not data.get("fechaCreacion"):
            return jsonify({"error": "Faltan datos"}), 400
        resultado = GruposService.update(id_grupo, data)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)   
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@grupos_bp.route("/getGrupo/<int:id_grupo>", methods=["GET"])
def get_grupo(id_grupo):
    """
    Obtener detalles de un grupo por su ID
    ---
    parameters:
      - name: id_grupo
        in: path
        type: integer
        required: true
        description: El ID único del grupo que deseas consultar.
    responses:
      200:
        description: Detalles del grupo obtenidos correctamente.
        schema:
          type: object
      500:
        description: Error interno del servidor.
    """
    try:
        resultado = GruposService.get_grupo(id_grupo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@grupos_bp.route("/deleteGrupo/<int:id_grupo>", methods=["DELETE"])
def delete_grupo(id_grupo):
    """
    Delete grupo
    ---
    parameters:
      - name: id_grupo
        in: path
        type: integer
        required: true
        description: Parámetro id_grupo
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = GruposService.delete(id_grupo)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500