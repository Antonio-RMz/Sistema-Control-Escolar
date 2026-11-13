from flask import Blueprint, request, jsonify
from app.services.personal_service import PersonalService
from app.utils.seguridad import error_interno

personal_bp = Blueprint("personal", __name__)


def _respuesta(resultado, ok_status=200):
    if "error" in resultado:
        return jsonify({"error": resultado["error"]}), resultado.pop("_status", 400)
    return jsonify(resultado), ok_status


@personal_bp.route("/personal", methods=["GET"])
def get_personales():
    """
    Lista paginada de cuentas de personal (sin contraseñas)
    ---
    parameters:
      - {name: page, in: query, type: integer, required: false}
      - {name: limit, in: query, type: integer, required: false, description: "máx. 500"}
      - {name: search, in: query, type: string, required: false}
      - {name: status, in: query, type: string, required: false}
    responses:
      200: {description: "data, page, limit, total, total_pages"}
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()
        status = request.args.get("status")
        return jsonify(PersonalService.get_personales(page, limit, search, status))
    except Exception as e:
        return error_interno(e, "listar personal")


@personal_bp.route("/personal", methods=["POST"])
def create_personal():
    """
    Crear cuenta de personal. "password" llega en texto plano y la API la cifra.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre: {type: string}
            usuario: {type: string}
            password: {type: string}
            rol: {type: string}
            permisos_modulos: {type: string, description: "vacío = sin permisos"}
    responses:
      201: {description: Creada}
      400: {description: Datos inválidos}
    """
    try:
        data = request.json or {}
        if not data.get("nombre") or not data.get("usuario") or not data.get("password") or not data.get("rol"):
            return jsonify({"error": "Faltan datos obligatorios (nombre, usuario, password, rol)"}), 400
        return _respuesta(PersonalService.create_personal(data), 201)
    except Exception as e:
        return error_interno(e, "crear personal")


@personal_bp.route("/personal/<int:idPersonal>", methods=["GET"])
def get_personal_by_id(idPersonal):
    """
    Detalle de una cuenta de personal (sin contraseña)
    ---
    parameters:
      - {name: idPersonal, in: path, type: integer, required: true}
    responses:
      200: {description: OK}
      404: {description: No encontrada}
    """
    try:
        personal = PersonalService.get_personal_by_id(idPersonal)
        if not personal:
            return jsonify({"error": "Cuenta de personal no encontrada"}), 404
        return jsonify({"success": True, "data": personal})
    except Exception as e:
        return error_interno(e, "detalle personal")


@personal_bp.route("/personal/<int:idPersonal>/acceso", methods=["GET"])
def get_acceso_personal(idPersonal):
    """
    Estado y permisos vigentes de la cuenta (Laravel lo consulta para revalidar sesiones abiertas)
    ---
    parameters:
      - {name: idPersonal, in: path, type: integer, required: true}
    responses:
      200: {description: "status, permisos_modulos"}
      404: {description: No encontrada}
    """
    try:
        p = PersonalService.get_personal_by_id(idPersonal)
        if not p:
            return jsonify({"error": "Cuenta de personal no encontrada"}), 404
        return jsonify({"success": True, "data": {"status": p["status"], "permisos_modulos": p["permisos_modulos"] or "", "rol": p["rol"]}})
    except Exception as e:
        return error_interno(e, "acceso personal")


@personal_bp.route("/personal/<int:idPersonal>", methods=["PUT"])
def update_personal(idPersonal):
    """
    Actualizar cuenta de personal ("password" opcional, en texto plano)
    ---
    parameters:
      - {name: idPersonal, in: path, type: integer, required: true}
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre: {type: string}
            usuario: {type: string}
            rol: {type: string}
            status: {type: string}
    responses:
      200: {description: OK}
      400: {description: Datos inválidos}
      404: {description: No encontrada}
    """
    try:
        data = request.json or {}
        if not data.get("nombre") or not data.get("usuario") or not data.get("rol") or not data.get("status"):
            return jsonify({"error": "Faltan datos obligatorios (nombre, usuario, rol, status)"}), 400
        return _respuesta(PersonalService.update_personal(idPersonal, data))
    except Exception as e:
        return error_interno(e, "editar personal")


@personal_bp.route("/personal/<int:idPersonal>", methods=["DELETE"])
def delete_personal(idPersonal):
    """
    Desactivar cuenta de personal (baja lógica: status = INACTIVO)
    ---
    parameters:
      - {name: idPersonal, in: path, type: integer, required: true}
    responses:
      200: {description: Desactivada}
      404: {description: No encontrada}
    """
    try:
        return _respuesta(PersonalService.desactivar_personal(idPersonal))
    except Exception as e:
        return error_interno(e, "desactivar personal")


@personal_bp.route("/personal/login", methods=["POST"])
def login_personal():
    """
    Verificar credenciales de personal. La contraseña se compara en la API; nunca se devuelve el hash.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            usuario: {type: string}
            password: {type: string}
    responses:
      200: {description: "Credenciales válidas: datos de la cuenta"}
      401: {description: "Contraseña incorrecta"}
      403: {description: "Cuenta inactiva o sin contraseña"}
      404: {description: "No existe"}
    """
    try:
        data = request.json or {}
        estado, datos = PersonalService.login(data.get("usuario"), data.get("password"))
        respuestas = {
            "ok": ({"success": True, "data": datos}, 200),
            "no_existe": ({"error": "Cuenta no encontrada", "motivo": estado}, 404),
            "inactivo": ({"error": "La cuenta de personal se encuentra inactiva", "motivo": estado}, 403),
            "sin_password": ({"error": "Esta cuenta aún no tiene contraseña asignada", "motivo": estado}, 403),
            "password": ({"error": "Contraseña incorrecta", "motivo": estado}, 401),
        }
        cuerpo, codigo = respuestas[estado]
        return jsonify(cuerpo), codigo
    except Exception as e:
        return error_interno(e, "login personal")


@personal_bp.route("/personal/by-username/<string:username>", methods=["GET"])
def get_personal_by_username(username):
    """
    Datos públicos de una cuenta activa (ya NO incluye la contraseña; usar POST /personal/login)
    ---
    parameters:
      - {name: username, in: path, type: string, required: true}
    responses:
      200: {description: OK}
      404: {description: No encontrada o inactiva}
    """
    try:
        personal = PersonalService.get_personal_by_username(username)
        if not personal:
            return jsonify({"error": "Cuenta de personal no encontrada o inactiva"}), 404
        return jsonify({"success": True, "data": personal})
    except Exception as e:
        return error_interno(e, "personal por usuario")
