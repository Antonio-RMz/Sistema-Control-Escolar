from flask import Blueprint, jsonify, request
from app.services.docentes_service import DocentesService

docentes_bp = Blueprint("docentes", __name__)


# Métodos get para docentes
@docentes_bp.route("/createDocentes", methods=["POST"])
def create_docente():
    """
    Create docente
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: Parámetro page
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        # Obtener datos del body (JSON)
        data = request.get_json()

        # Validar que venga información
        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        #  Validar x obligatorios
        required_fields = ["nombreDocente", "statusDocente"]

        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"error": f"Falta el campo {field}"}), 400

        #  Llamar al service (lógica de negocio)
        resultado = DocentesService.create_docente(data)

        #  Si el service regresa error
        if "error" in resultado:
            return jsonify(resultado), 500

        # Todo correcto
        return jsonify(resultado), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Método para crear un nuevo docente
@docentes_bp.route("/docentes", methods=["GET"])
def get_docentes():
    """
    Get docentes
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
            nombreDocente:
              type: string
            statusDocente:
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
        status = request.args.get("status")  # opcional filtro

        resultado = DocentesService.get_docentes(page, limit, search, status)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/updateDocente/<int:id_docente>", methods=["PUT"])
def update_docente(id_docente):
    """
    Update docente
    ---
    parameters:
      - name: id_docente
        in: path
        type: integer
        required: true
        description: Parámetro id_docente
      - name: fecha_inicio
        in: query
        type: string
        required: false
        description: Parámetro fecha_inicio
      - name: fecha_fin
        in: query
        type: string
        required: false
        description: Parámetro fecha_fin
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombreDocente:
              type: string
            statusDocente:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if (
            not data.get("nombreDocente")
            or not data.get("statusDocente")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(DocentesService.update_docente(id_docente, data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/deleteDocente/<int:idDocente>", methods=["DELETE"])
def delete_docente(idDocente):
    """
    Delete docente
    ---
    parameters:
      - name: idDocente
        in: path
        type: integer
        required: true
        description: Parámetro idDocente
      - name: fecha_inicio
        in: query
        type: string
        required: false
        description: Parámetro fecha_inicio
      - name: fecha_fin
        in: query
        type: string
        required: false
        description: Parámetro fecha_fin
      - name: fecha
        in: query
        type: string
        required: false
        description: Parámetro fecha
      - name: id_docente
        in: query
        type: string
        required: false
        description: Parámetro id_docente
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(DocentesService.delete_docente(idDocente))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/horasDocentes", methods=["GET"])
def get_horas_docentes():
    """
    Get horas docentes
    ---
    parameters:
      - name: fecha_inicio
        in: query
        type: string
        required: false
        description: Parámetro fecha_inicio
      - name: fecha_fin
        in: query
        type: string
        required: false
        description: Parámetro fecha_fin
      - name: fecha
        in: query
        type: string
        required: false
        description: Parámetro fecha
      - name: id_docente
        in: query
        type: string
        required: false
        description: Parámetro id_docente
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        fecha_inicio = request.args.get("fecha_inicio")
        fecha_fin = request.args.get("fecha_fin")
        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan parámetros fecha_inicio o fecha_fin"}), 400
        
        resultado = DocentesService.get_horas_docentes(fecha_inicio, fecha_fin)
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/detalleHorasDocente", methods=["GET"])
def get_detalle_horas_docente():
    """
    Get detalle horas docente
    ---
    parameters:
      - name: fecha
        in: query
        type: string
        required: false
        description: Parámetro fecha
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
            usuario:
              type: string
            password:
              type: string
            permisos_modulos:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        fecha = request.args.get("fecha")
        id_docente = request.args.get("id_docente")
        if not fecha or not id_docente:
            return jsonify({"error": "Faltan parámetros fecha o id_docente"}), 400
        
        resultado = DocentesService.get_detalle_horas_docente(id_docente, fecha)
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/docentes/<int:idDocente>/credenciales", methods=["POST"])
def actualizar_credenciales_docente(idDocente):
    """
    Actualizar credenciales docente
    ---
    parameters:
      - name: idDocente
        in: path
        type: integer
        required: true
        description: Parámetro idDocente
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            usuario:
              type: string
            password:
              type: string
            permisos_modulos:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json() or {}
        usuario = data.get("usuario")
        password = data.get("password")
        permisos_modulos = data.get("permisos_modulos")

        if not usuario:
            return jsonify({"error": "El nombre de usuario es obligatorio"}), 400

        resultado = DocentesService.actualizar_credenciales(idDocente, usuario, password, permisos_modulos)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/docentes/by-username/<string:username>", methods=["GET"])
def get_docente_by_username(username):
    """
    Get docente by username
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
        docente = DocentesService.get_docente_by_username(username)
        if not docente:
            return jsonify({"error": "Docente no encontrado"}), 404
        return jsonify({"success": True, "data": docente})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/docentes/<int:idDocente>/pendientes", methods=["GET"])
def get_docente_pendientes(idDocente):
    """
    Get pending items for a teacher (prorrogas, finalizando, calificaciones)
    ---
    parameters:
      - name: idDocente
        in: path
        type: integer
        required: true
        description: ID del docente
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = DocentesService.get_docente_pendientes(idDocente)
        if "error" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
