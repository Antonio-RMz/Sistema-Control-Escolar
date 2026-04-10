from flask import Blueprint, jsonify, request
from app.services.alumnos_service import AlumnosService

alumnos_bp = Blueprint('alumnos', __name__)

@alumnos_bp.route('/alumnos', methods=['GET'])
def get_alumnos():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        idGeneracion = request.args.get('idGeneracion')
        idGrupo = request.args.get('idGrupo')
        search = request.args.get('search', '').strip()

        resultado = AlumnosService.get_alumnos(page, limit, idGeneracion, idGrupo, search)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alumnos_bp.route('/crealumnos', methods=['POST'])
def create_alumno():
    try:
        data = request.json
        if not data.get('nombre') or not data.get('apPaterno'):
            return jsonify({"error": "Faltan datos"}), 400
        
        resultado = AlumnosService.create_alumno(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
