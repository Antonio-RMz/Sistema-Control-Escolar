from flask import Blueprint, jsonify
from app.services.notificaciones_service import NotificacionesService

notificaciones_bp = Blueprint("notificaciones", __name__)

@notificaciones_bp.route("/notificaciones", methods=["GET"])
def get_notificaciones():
    """
    Obtener lista de avisos y tareas pendientes
    ---
    responses:
      200:
        description: Retorna un objeto con la lista de avisos y tareas pendientes.
        schema:
          type: object
          properties:
            avisos:
              type: array
              items:
                type: object
            pendientes:
              type: array
              items:
                type: object
      500:
        description: Error interno del servidor.
    """
    try:
        res = NotificacionesService.obtener_avisos_y_pendientes()
        if "error" in res:
            return jsonify({"error": res["error"]}), 500
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
