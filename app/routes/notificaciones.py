from flask import Blueprint, jsonify, request
from app.services.notificaciones_service import NotificacionesService

notificaciones_bp = Blueprint("notificaciones", __name__)

@notificaciones_bp.route("/notificaciones", methods=["GET"])
def get_notificaciones():
    """
    Obtener lista de avisos y tareas pendientes
    """
    try:
        res = NotificacionesService.obtener_avisos_y_pendientes()
        if "error" in res:
            return jsonify({"error": res["error"]}), 500
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notificaciones_bp.route("/notificaciones/resolver", methods=["POST"])
def resolver_notificacion():
    """
    Marcar una advertencia como resuelta o ignorada (no es alerta)
    """
    try:
        data = request.json or {}
        tipo = data.get("tipo")
        id_referencia = data.get("id_referencia")
        accion = data.get("accion", "resuelto")  # 'resuelto' o 'ignorar'
        subtipo = data.get("subtipo", "general")
        motivo = data.get("motivo")
        usuario = data.get("usuario")

        if not tipo or id_referencia is None:
            return jsonify({"error": "Parámetros incompletos (tipo, id_referencia)"}), 400

        res = NotificacionesService.resolver_alerta(
            tipo=tipo,
            id_referencia=int(id_referencia),
            accion=accion,
            subtipo=subtipo,
            motivo=motivo,
            usuario=usuario
        )

        if "error" in res:
            return jsonify({"error": res["error"]}), 500
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notificaciones_bp.route("/notificaciones/reactivar", methods=["POST"])
def reactivar_notificacion():
    """
    Reactivar una advertencia previamente resuelta u omitida
    """
    try:
        data = request.json or {}
        tipo = data.get("tipo")
        id_referencia = data.get("id_referencia")
        subtipo = data.get("subtipo", "general")

        if not tipo or id_referencia is None:
            return jsonify({"error": "Parámetros incompletos (tipo, id_referencia)"}), 400

        res = NotificacionesService.reactivar_alerta(
            tipo=tipo,
            id_referencia=int(id_referencia),
            subtipo=subtipo
        )

        if "error" in res:
            return jsonify({"error": res["error"]}), 500
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
