from flask import Blueprint, jsonify, request
from app.services.reportes_indisciplina_service import ReportesIndisciplinaService

reportes_indisciplina_bp = Blueprint("reportes_indisciplina", __name__)

@reportes_indisciplina_bp.route("/reportes-indisciplina", methods=["GET"])
def listar_reportes():
    try:
        id_alumno = request.args.get("id_alumno")
        search = request.args.get("search")
        page = request.args.get("page", 1)
        limit = request.args.get("limit", 15)

        resultado = ReportesIndisciplinaService.listar_reportes(
            id_alumno=id_alumno,
            search=search,
            page=page,
            limit=limit
        )
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@reportes_indisciplina_bp.route("/reportes-indisciplina", methods=["POST"])
def crear_reporte():
    try:
        data = request.get_json() or {}
        resultado, status = ReportesIndisciplinaService.crear_reporte(data)
        return jsonify(resultado), status
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@reportes_indisciplina_bp.route("/reportes-indisciplina/<int:id>", methods=["DELETE"])
def eliminar_reporte(id):
    try:
        resultado, status = ReportesIndisciplinaService.eliminar_reporte(id)
        return jsonify(resultado), status
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@reportes_indisciplina_bp.route("/reportes-indisciplina/conteo/<int:id_alumno>", methods=["GET"])
@reportes_indisciplina_bp.route("/alumnos/<int:id_alumno>/reportes-conteo", methods=["GET"])
def obtener_conteo(id_alumno):
    try:
        resultado = ReportesIndisciplinaService.obtener_conteo_alumno(id_alumno)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
