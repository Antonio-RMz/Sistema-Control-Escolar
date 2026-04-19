from flask import Blueprint, jsonify, request
from app.services.alumnos_service import AlumnosService
from app.services.grupos_service import GruposService

alumnos_bp = Blueprint('alumnos', __name__)
# Método GET para consultar alumnos
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

@alumnos_bp.route('/<int:idGrupo>/alumnos', methods=['GET'])
def get_alumnos_by_grupo(idGrupo):
    try:
        # Usamos el servicio de grupos que ya hace el JOIN con tb_alumnogrupo
        alumnos = GruposService.get_alumnos_by_grupo(idGrupo)
        return jsonify(alumnos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# bloque para crar a un alumno
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

@alumnos_bp.route('/importar-alumnos-hoja', methods=['POST'])
def importar_alumnos_hoja():
    try:
        data = request.json or {}
        # n_hoja es 1-indexed para el usuario (ej: 38 para la hoja 38)
        # internamente restamos 1 para que sea 0-indexed para pandas (37)
        n_hoja = data.get('n_hoja', 38) 
        id_gen = data.get('id_generacion', 38)
        
        sheet_index = n_hoja - 1
        
        resultado = AlumnosService.importar_alumnos_hoja(sheet_index, id_gen)
        return jsonify(resultado), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
