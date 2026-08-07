from flask import Blueprint, jsonify, request
from app.services.docentes_service import DocentesService

docentes_bp = Blueprint("docentes", __name__)


# Métodos get para docentes
@docentes_bp.route("/createDocentes", methods=["POST"])
def create_docente():
    try:
        # Obtener datos del body (JSON)
        data = request.get_json()

        # Validar que venga información
        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        #  Validar x obligatorios
        required_fields = ["nombreDocente", "statusDocente"]

        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"error": f"Falta el campo {field}"}), 400

        #  Llamar al service (lógica de negocio)
        resultado = DocentesService.create_docente(data)

        #  Si el service regresa error
        if "error" in resultado:
            return jsonify(resultado), 500

        # Todo correcto
        return jsonify(resultado), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Método para crear un nuevo docente
@docentes_bp.route("/docentes", methods=["GET"])
def get_docentes():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()
        status = request.args.get("status")  # opcional filtro

        resultado = DocentesService.get_docentes(page, limit, search, status)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/updateDocente/<int:id_docente>", methods=["PUT"])
def update_docente(id_docente):
    try:
        data = request.json
        if (
            not data.get("nombreDocente")
            or not data.get("statusDocente")
        ):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(DocentesService.update_docente(id_docente, data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/deleteDocente/<int:idDocente>", methods=["DELETE"])
def delete_docente(idDocente):
    try:
        return jsonify(DocentesService.delete_docente(idDocente))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/horasDocentes", methods=["GET"])
def get_horas_docentes():
    try:
        fecha_inicio = request.args.get("fecha_inicio")
        fecha_fin = request.args.get("fecha_fin")
        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan parámetros fecha_inicio o fecha_fin"}), 400
        
        resultado = DocentesService.get_horas_docentes(fecha_inicio, fecha_fin)
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@docentes_bp.route("/detalleHorasDocente", methods=["GET"])
def get_detalle_horas_docente():
    try:
        fecha = request.args.get("fecha")
        id_docente = request.args.get("id_docente")
        if not fecha or not id_docente:
            return jsonify({"error": "Faltan parámetros fecha o id_docente"}), 400
        
        resultado = DocentesService.get_detalle_horas_docente(id_docente, fecha)
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
