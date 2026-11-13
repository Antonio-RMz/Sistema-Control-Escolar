"""
Usuarios administrativos (tb_users): admin / coordinador.
Laravel los autentica con Auth::attempt a través de un UserProvider que consume estos endpoints.
Ningún endpoint devuelve el hash de la contraseña.
"""
from flask import Blueprint, jsonify, request

from app.config.conexion import get_connection
from app.utils.seguridad import (
    auditar, error_interno, es_hash, hash_password, usuario_en_uso, validar_password_nueva, verificar_password,
)

usuarios_bp = Blueprint("usuarios", __name__)

_COLUMNAS = "id, name, usuario, email, rol, activo, ultimo_acceso, created_at, updated_at"
_ROLES = ("admin", "coordinador")


def _uno(sql, params):
    conexion = get_connection()
    cursor = conexion.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


@usuarios_bp.route("/usuarios/<int:id_usuario>", methods=["GET"])
def obtener_usuario(id_usuario):
    """
    Usuario administrativo por id (sin contraseña)
    ---
    parameters:
      - {name: id_usuario, in: path, type: integer, required: true}
    responses:
      200: {description: OK}
      404: {description: No encontrado}
    """
    try:
        u = _uno(f"SELECT {_COLUMNAS} FROM tb_users WHERE id = %s", (id_usuario,))
        return (jsonify({"success": True, "data": u}), 200) if u else (jsonify({"error": "Usuario no encontrado"}), 404)
    except Exception as e:
        return error_interno(e, "obtener usuario")


@usuarios_bp.route("/usuarios/by-username/<string:usuario>", methods=["GET"])
def obtener_por_usuario(usuario):
    """
    Usuario administrativo por nombre de usuario (sin contraseña)
    ---
    parameters:
      - {name: usuario, in: path, type: string, required: true}
    responses:
      200: {description: OK}
      404: {description: No encontrado}
    """
    try:
        u = _uno(f"SELECT {_COLUMNAS} FROM tb_users WHERE usuario = %s", (usuario.strip(),))
        return (jsonify({"success": True, "data": u}), 200) if u else (jsonify({"error": "Usuario no encontrado"}), 404)
    except Exception as e:
        return error_interno(e, "usuario por nombre")


@usuarios_bp.route("/usuarios/login", methods=["POST"])
def login_usuario():
    """
    Verificar credenciales de un usuario administrativo (la comparación ocurre en la API)
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
      200: {description: "Válidas: datos del usuario"}
      401: {description: "Contraseña incorrecta"}
      403: {description: "Usuario inactivo"}
      404: {description: "No existe"}
    """
    conexion = None
    try:
        data = request.json or {}
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS}, password FROM tb_users WHERE usuario = %s", ((data.get("usuario") or "").strip(),))
        u = cursor.fetchone()
        if not u:
            return jsonify({"error": "Usuario no encontrado", "motivo": "no_existe"}), 404
        hash_guardado = u.pop("password", None)
        if not u["activo"]:
            return jsonify({"error": "Usuario inactivo", "motivo": "inactivo"}), 403
        if not verificar_password(data.get("password"), hash_guardado):
            return jsonify({"error": "Contraseña incorrecta", "motivo": "password"}), 401
        cursor.execute("UPDATE tb_users SET ultimo_acceso = NOW() WHERE id = %s", (u["id"],))
        conexion.commit()
        cursor.close()
        return jsonify({"success": True, "data": u})
    except Exception as e:
        return error_interno(e, "login usuario")
    finally:
        if conexion:
            conexion.close()


@usuarios_bp.route("/usuarios", methods=["POST"])
def crear_usuario():
    """
    Crear usuario administrativo. Acepta "password" (texto plano, se cifra aquí) o
    "password_hash" (bcrypt ya cifrado, para migrar cuentas existentes sin conocer la contraseña).
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name: {type: string}
            usuario: {type: string}
            rol: {type: string, enum: [admin, coordinador]}
            activo: {type: boolean}
            password: {type: string}
            password_hash: {type: string}
    responses:
      201: {description: Creado}
      400: {description: Datos inválidos}
      409: {description: Usuario en uso}
    """
    conexion = None
    try:
        data = request.json or {}
        usuario = (data.get("usuario") or "").strip()
        rol = data.get("rol") or "coordinador"
        if not usuario or not (data.get("name") or "").strip():
            return jsonify({"error": "Faltan datos obligatorios (name, usuario)"}), 400
        if rol not in _ROLES:
            return jsonify({"error": "Rol inválido"}), 400

        if data.get("password_hash"):
            if not es_hash(data["password_hash"]):
                return jsonify({"error": "password_hash no es un hash bcrypt válido"}), 400
            hash_final = data["password_hash"]
        else:
            error_pw = validar_password_nueva(data.get("password"))
            if error_pw:
                return jsonify({"error": error_pw}), 400
            hash_final = hash_password(data["password"])

        conexion = get_connection()
        cursor = conexion.cursor()
        en_uso = usuario_en_uso(cursor, usuario)
        if en_uso:
            return jsonify({"error": f"El nombre de usuario ya está asignado a {en_uso}."}), 409

        cursor.execute(
            "INSERT INTO tb_users (name, usuario, email, password, rol, activo, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (data["name"].strip(), usuario, data.get("email") or None, hash_final, rol, 1 if data.get("activo", True) else 0),
        )
        conexion.commit()
        auditar("usuario.crear", id=cursor.lastrowid, cuenta=usuario, rol=rol)
        return jsonify({"success": True, "id": cursor.lastrowid}), 201
    except Exception as e:
        return error_interno(e, "crear usuario")
    finally:
        if conexion:
            conexion.close()


@usuarios_bp.route("/usuarios/<int:id_usuario>/password", methods=["PUT"])
def cambiar_password(id_usuario):
    """
    Cambiar contraseña (texto plano; se cifra aquí). La regla del correo maestro para cuentas
    admin la valida Laravel (RestablecerPasswordService) antes de llamar este endpoint.
    ---
    parameters:
      - {name: id_usuario, in: path, type: integer, required: true}
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            password: {type: string}
    responses:
      200: {description: OK}
      400: {description: Contraseña inválida}
      404: {description: No encontrado}
    """
    conexion = None
    try:
        data = request.json or {}
        error_pw = validar_password_nueva(data.get("password"))
        if error_pw:
            return jsonify({"error": error_pw}), 400
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE tb_users SET password = %s, remember_token = NULL, updated_at = NOW() WHERE id = %s",
            (hash_password(data["password"]), id_usuario),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404
        auditar("usuario.password", id=id_usuario)
        return jsonify({"success": True})
    except Exception as e:
        return error_interno(e, "cambiar password usuario")
    finally:
        if conexion:
            conexion.close()
