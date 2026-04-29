from flask import Blueprint, jsonify, request
from app.services.catalogos_service import CatalogosService
from app.services.grupos_service import GruposService

catalogos_bp = Blueprint("catalogos", __name__)


@catalogos_bp.route("/centroTrabajo", methods=["GET"])
def get_centro_trabajo():
    try:
        return jsonify(CatalogosService.get_centros_trabajo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/getAlumnoEquivalencia", methods=["GET"])
def get_alumno_equivalencia():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()

        resultado = CatalogosService.get_alumno_equivalencia(page, limit, search)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createCentroTrabajo", methods=["POST"])
def create_centro_trabajo():
    try:
        data = request.json
        if not data.get("clave") or not data.get("nombre"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_centro_trabajo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/tipoPeriodo", methods=["GET"])
def get_tipo_periodo():
    try:
        return jsonify(CatalogosService.get_tipos_periodo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createTipoPeriodo", methods=["POST"])
def create_tipo_periodo():
    try:
        data = request.json
        if not data.get("nombrePeriodo") or not data.get("descripcionPeriodo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_tipo_periodocreate_tipo_periodo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/materias", methods=["GET"])
def get_materias():
    try:
        return jsonify(CatalogosService.get_materias())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createMateria", methods=["POST"])
def create_materia():
    try:
        data = request.json

        if not data.get("nombreMateria") or not data.get("estatusMateria"):
            return jsonify({"error": "Faltan datos"}), 400

        # Validar que docentes sea lista si viene
        if "docentes" in data and not isinstance(data.get("docentes"), list):
            return jsonify({"error": "docentes debe ser una lista"}), 400

        return jsonify(CatalogosService.create_materia(data))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Métodos get para docentes
@catalogos_bp.route("/createDocentes", methods=["POST"])
def create_docente():
    try:
        # 📥 Obtener datos del body (JSON)
        data = request.get_json()

        # ⚠️ Validar que venga información
        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        # 🧪 Validar x obligatorios
        required_fields = ["nombreDocente", "statusDocente"]

        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"error": f"Falta el campo {field}"}), 400

        # 🧠 Llamar al service (lógica de negocio)
        resultado = CatalogosService.create_docente(data)

        # ❌ Si el service regresa error
        if "error" in resultado:
            return jsonify(resultado), 500

        # ✅ Todo correcto
        return jsonify(resultado), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Método para crear un nuevo docente
@catalogos_bp.route("/docentes", methods=["GET"])
def get_docentes():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()
        status = request.args.get("status")  # opcional filtro

        resultado = CatalogosService.get_docentes(page, limit, search, status)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createPlanEstudios", methods=["POST"])
def create_plan_estudios():
    try:
        data = request.json
        if (
            not data.get("nombrePlan")
            or not data.get("descripcionPlan")
            or not data.get("estatusPlan")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_plan_estudios(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/getPlanesEstudio", methods=["GET"])
def get_planes_estudio():
    try:
        return jsonify(CatalogosService.get_planes_estudio())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createAlumnoGrupo", methods=["POST"])
def create_alumno_grupo():
    try:
        data = request.json
        if not data.get("idAlumno") or not data.get("idGrupo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_alumno_grupo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

        return jsonify(CatalogosService.create_alumno_grupo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/createCursoExtra", methods=["POST"])
def create_curso_extracurricular():
    try:
        data = request.json
        if (
            not data.get("nombre")
            or not data.get("idCentroTrabajo")
            or not data.get("idDocente")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(CatalogosService.create_curso_extracurricular(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalogos_bp.route("/getCursosExtra", methods=["GET"])
def get_cursos_extracurriculares():
    try:
        return jsonify(CatalogosService.get_cursos_extracurriculares())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
