from flask import Blueprint, request, jsonify
from app.services.personal_service import PersonalService

personal_bp = Blueprint("personal", __name__)

@personal_bp.route("/personal", methods=["GET"])
def get_personales():
    """
    Get personales
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
      - name: status
        in: query
        type: string
        required: false
        description: Parámetro status
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            usuario:
              type: string
            password:
              type: string
            rol:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()
        status = request.args.get("status")

        resultado = PersonalService.get_personales(page, limit, search, status)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@personal_bp.route("/personal", methods=["POST"])
def create_personal():
    """
    Create personal
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            usuario:
              type: string
            password:
              type: string
            rol:
              type: string
            status:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        if not data.get("nombre") or not data.get("usuario") or not data.get("password") or not data.get("rol"):
            return jsonify({"error": "Faltan datos obligatorios (nombre, usuario, password, rol)"}), 400

        resultado = PersonalService.create_personal(data)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@personal_bp.route("/personal/<int:idPersonal>", methods=["GET"])
def get_personal_by_id(idPersonal):
    """
    Get personal by id
    ---
    parameters:
      - name: idPersonal
        in: path
        type: integer
        required: true
        description: Parámetro idPersonal
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            usuario:
              type: string
            rol:
              type: string
            status:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        personal = PersonalService.get_personal_by_id(idPersonal)
        if not personal:
            return jsonify({"error": "Cuenta de personal no encontrada"}), 404
        return jsonify({"success": True, "data": personal})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@personal_bp.route("/personal/<int:idPersonal>", methods=["PUT"])
def update_personal(idPersonal):
    """
    Update personal
    ---
    parameters:
      - name: idPersonal
        in: path
        type: integer
        required: true
        description: Parámetro idPersonal
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            usuario:
              type: string
            rol:
              type: string
            status:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        if not data.get("nombre") or not data.get("usuario") or not data.get("rol") or not data.get("status"):
            return jsonify({"error": "Faltan datos obligatorios (nombre, usuario, rol, status)"}), 400

        resultado = PersonalService.update_personal(idPersonal, data)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@personal_bp.route("/personal/<int:idPersonal>", methods=["DELETE"])
def delete_personal(idPersonal):
    """
    Delete personal
    ---
    parameters:
      - name: idPersonal
        in: path
        type: integer
        required: true
        description: Parámetro idPersonal
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = PersonalService.delete_personal(idPersonal)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@personal_bp.route("/personal/by-username/<string:username>", methods=["GET"])
def get_personal_by_username(username):
    """
    Get personal by username
    ---
    parameters:
      - name: username
        in: path
        type: string
        required: true
        description: Parámetro username
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        personal = PersonalService.get_personal_by_username(username)
        if not personal:
            return jsonify({"error": "Cuenta de personal no encontrada o inactiva"}), 404
        return jsonify({"success": True, "data": personal})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
