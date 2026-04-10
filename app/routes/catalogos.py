from flask import Blueprint, jsonify, request
from app.services.catalogos_service import CatalogosService

catalogos_bp = Blueprint('catalogos', __name__)

@catalogos_bp.route('/centroTrabajo', methods=['GET'])
def get_centro_trabajo():
    try:
        return jsonify(CatalogosService.get_centros_trabajo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/createCentroTrabajo', methods=['POST'])
def create_centro_trabajo():
    try:
        data = request.json
        if not data.get('clave') or not data.get('nombre'):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_centro_trabajo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/tipoPeriodo', methods=['GET'])
def get_tipo_periodo():
    try:
        return jsonify(CatalogosService.get_tipos_periodo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/createTipoPeriodo', methods=['POST'])
def create_tipo_periodo():
    try:
        data = request.json
        if not data.get('nombrePeriodo') or not data.get('descripcionPeriodo'):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_tipo_periodo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/materias', methods=['GET'])
def get_materias():
    try:
        return jsonify(CatalogosService.get_materias())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/createMateria', methods=['POST'])
def create_materia():
    try:
        data = request.json
        if not data.get('nombreMateria') or not data.get('idDocente') or not data.get('estatusMateria'):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_materia(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/docentes', methods=['GET'])
def get_docentes():
    try:
        return jsonify(CatalogosService.get_docentes())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/createDocente', methods=['POST'])
def create_docente():
    try:
        data = request.json
        if not data.get('nombreDocente') or not data.get('apPaternoDocente') or not data.get('apMaternoDocente') or not data.get('correoDocente') or not data.get('telefonoDocente'):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_docente(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@catalogos_bp.route('/createPlanEstudios', methods=['POST'])
def create_plan_estudios():
    try:
        data = request.json
        if not data.get('nombrePlan') or not data.get('descripcionPlan') or not data.get('estatusPlan'):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_plan_estudios(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
