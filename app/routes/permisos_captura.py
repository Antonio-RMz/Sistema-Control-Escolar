from flask import Blueprint, jsonify, request
from app.services.permisos_captura_service import PermisosCapturaService

permisos_captura_bp = Blueprint("permisos_captura", __name__)

@permisos_captura_bp.route("/permisos-captura/lista", methods=["GET"])
def obtener_lista():
    try:
        resultado = PermisosCapturaService.obtener_lista_permisos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/matriz", methods=["GET"])
def obtener_matriz():
    try:
        resultado = PermisosCapturaService.obtener_matriz_avance()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/docentes", methods=["GET"])
def obtener_docentes():
    try:
        resultado = PermisosCapturaService.obtener_docentes_activos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/grupos", methods=["GET"])
def obtener_grupos():
    try:
        resultado = PermisosCapturaService.obtener_grupos_activos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura", methods=["POST"])
def guardar_permiso():
    try:
        data = request.get_json()
        resultado = PermisosCapturaService.guardar_permiso(data)
        if not resultado.get("success"):
            return jsonify(resultado), 422
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/<int:id>", methods=["PUT"])
def actualizar_permiso(id):
    try:
        data = request.get_json()
        resultado = PermisosCapturaService.actualizar_permiso(id, data)
        if not resultado.get("success"):
            return jsonify(resultado), 422
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/<int:id>", methods=["DELETE"])
def eliminar_permiso(id):
    try:
        resultado = PermisosCapturaService.eliminar_permiso(id)
        if not resultado.get("success"):
            return jsonify(resultado), 422
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/ccts", methods=["GET"])
def obtener_ccts():
    try:
        resultado = PermisosCapturaService.obtener_ccts()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/cct/<int:cct_id>/grupos", methods=["GET"])
def obtener_grupos_por_cct(cct_id):
    try:
        resultado = PermisosCapturaService.obtener_grupos_por_cct(cct_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/grupo-config/<int:grupo_id>", methods=["GET"])
def obtener_grupo_config(grupo_id):
    try:
        resultado = PermisosCapturaService.obtener_grupo_config(grupo_id)
        if not resultado.get("success"):
            return jsonify(resultado), 404
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@permisos_captura_bp.route("/permisos-captura/grupo-config/<int:grupo_id>", methods=["POST"])
def guardar_grupo_config(grupo_id):
    try:
        data = request.get_json()
        resultado = PermisosCapturaService.guardar_grupo_config(grupo_id, data)
        if not resultado.get("success"):
            return jsonify(resultado), 422
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
