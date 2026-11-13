"""
Utilidades de seguridad compartidas por la API.

- Token de servicio: Laravel es el único cliente; cada petición debe traer X-API-Token = API_TOKEN.
- Contraseñas: bcrypt compatible con Laravel (Hash::make genera "$2y$", Python usa "$2b$").
- Errores: se registran completos en el log y al cliente se le devuelve un mensaje genérico.
- Bitácora: cambios sobre cuentas (quién, qué, cuándo) en logs/auditoria.log.
"""
import hmac
import logging
import os
from logging.handlers import RotatingFileHandler

import bcrypt
from flask import jsonify, request

log = logging.getLogger("api")

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

auditoria = logging.getLogger("auditoria")
if not auditoria.handlers:
    _h = RotatingFileHandler(os.path.join(_LOG_DIR, "auditoria.log"), maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    auditoria.addHandler(_h)
    auditoria.setLevel(logging.INFO)
    auditoria.propagate = False

if not log.handlers:
    _e = RotatingFileHandler(os.path.join(_LOG_DIR, "api.log"), maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    _e.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(_e)
    log.setLevel(logging.INFO)


# ---------------------------------------------------------------- token de servicio

# Rutas que no requieren token (documentación solo en modo debug)
_RUTAS_PUBLICAS_DEBUG = ("/apidocs", "/flasgger_static", "/apispec")


def registrar_token_api(app):
    """Exige X-API-Token en todas las peticiones si API_TOKEN está configurado."""
    token = os.getenv("API_TOKEN", "").strip()

    if not token:
        log.warning("API_TOKEN no configurado: la API acepta peticiones sin autenticar.")
        print("ADVERTENCIA: API_TOKEN no configurado; la API NO está protegida.")
        return

    @app.before_request
    def _verificar_token():
        if request.method == "OPTIONS":
            return None
        if app.debug and request.path.startswith(_RUTAS_PUBLICAS_DEBUG):
            return None
        recibido = request.headers.get("X-API-Token", "")
        if not hmac.compare_digest(recibido.encode(), token.encode()):
            return jsonify({"error": "No autorizado"}), 401
        return None


def usuario_solicitante():
    """Usuario de Laravel que originó la petición (cabecera X-Usuario), para la bitácora."""
    return (request.headers.get("X-Usuario") or "desconocido")[:100]


def auditar(accion, **datos):
    detalles = " ".join(f"{k}={v!r}" for k, v in datos.items())
    auditoria.info(f"usuario={usuario_solicitante()!r} accion={accion} {detalles}")


# ---------------------------------------------------------------- contraseñas

def es_hash(valor):
    return isinstance(valor, str) and valor.startswith(("$2y$", "$2b$", "$2a$")) and len(valor) == 60


def hash_password(plano):
    """Hash bcrypt con prefijo $2y$ para que Laravel (Hash::check) también lo acepte."""
    h = bcrypt.hashpw(plano.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()
    return "$2y$" + h[4:]


def verificar_password(plano, hash_guardado):
    if not plano or not es_hash(hash_guardado):
        return False
    try:
        h = "$2b$" + hash_guardado[4:]
        return bcrypt.checkpw(plano.encode("utf-8"), h.encode())
    except ValueError:
        return False


def validar_password_nueva(plano):
    """Mínimo 8 caracteres, con letras y números. Devuelve mensaje de error o None."""
    if not plano or len(plano) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isalpha() for c in plano) or not any(c.isdigit() for c in plano):
        return "La contraseña debe incluir letras y números."
    return None


# ---------------------------------------------------------------- errores

def error_interno(e, contexto=""):
    """Registra la excepción completa y responde un mensaje genérico (no exponer SQL/rutas)."""
    log.exception("Error interno %s: %s", contexto, e)
    return jsonify({"error": "Ocurrió un error interno. Intenta de nuevo o contacta al administrador."}), 500


# ---------------------------------------------------------------- unicidad de usuarios

def usuario_en_uso(cursor, usuario, excluir_tabla=None, excluir_id=None):
    """
    El login busca en tb_users → tb_docentes → tb_personal; un mismo nombre de usuario
    en dos tablas deja inaccesible una de las cuentas. Devuelve dónde está en uso o None.
    """
    u = (usuario or "").strip().lower()
    if not u:
        return None

    consultas = [
        ("tb_users", "SELECT id AS id FROM tb_users WHERE LOWER(usuario) = %s", "una cuenta de administrador"),
        ("tb_docentes", "SELECT idDocente AS id FROM tb_docentes WHERE LOWER(TRIM(usuario)) = %s OR LOWER(TRIM(correoDocente)) = %s", "un docente"),
        ("tb_personal", "SELECT idPersonal AS id FROM tb_personal WHERE LOWER(usuario) = %s", "otra cuenta de personal"),
    ]
    for tabla, sql, descripcion in consultas:
        try:
            cursor.execute(sql, (u, u) if sql.count("%s") == 2 else (u,))
        except Exception:
            continue  # p. ej. tb_users aún no existe en este entorno
        for fila in cursor.fetchall():
            if tabla == excluir_tabla and str(fila["id"]) == str(excluir_id):
                continue
            return descripcion
    return None
