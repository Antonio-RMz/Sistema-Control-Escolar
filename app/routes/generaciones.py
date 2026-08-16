from flask import Blueprint, jsonify, request
from app.services.generaciones_service import GeneracionesService

generaciones_bp = Blueprint("generaciones", __name__)


@generaciones_bp.route("/generaciones", methods=["GET"])
def get_generaciones():
    """
    Get generaciones
    ---
    parameters:
      - name: idCentroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro idCentroTrabajo
      - name: id_centroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centroTrabajo
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            idCentroTrabajo:
              type: string
            id_centroTrabajo:
              type: string
            anioFin:
              type: string
            aniofin:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo")
        resultado = GeneracionesService.get_all(id_centro_trabajo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generaciones_bp.route("/createGeneraciones", methods=["POST"])
@generaciones_bp.route("/generaciones", methods=["POST"])
def create_generacion():
    """
    Create generacion
    ---
    parameters:
      - name: idCentroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro idCentroTrabajo
      - name: id_centroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centroTrabajo
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            idCentroTrabajo:
              type: string
            id_centroTrabajo:
              type: string
            anioFin:
              type: string
            aniofin:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        cct = data.get("idCentroTrabajo") or data.get("id_centroTrabajo")
        fin_year = data.get("anioFin") or data.get("aniofin")
        
        if not all(field in data for field in ["nombreGeneracion", "generacion", "anioInicio", "mesInicio", "mesFin"]) or not cct or not fin_year:
            return jsonify({"error": "Faltan datos requeridos"}), 400

        resultado = GeneracionesService.create(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@generaciones_bp.route("/generaciones/ultima", methods=["GET"])
def get_ultima_generacion():
    """
    Get ultima generacion
    ---
    parameters:
      - name: idCentroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro idCentroTrabajo
      - name: id_centroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centroTrabajo
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centroTrabajo")
        if not id_centro_trabajo:
            return jsonify({"error": "Falta idCentroTrabajo"}), 400
        
        from app.config.conexion import get_connection
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, nombreGeneracion, generacion, anioInicio, aniofin, mesInicio, mesFin
                FROM tb_generaciones
                WHERE id_centroTrabajo = %s
                ORDER BY id DESC
                LIMIT 1
            """, (id_centro_trabajo,))
            row = cursor.fetchone()
            return jsonify(row)
        finally:
            cursor.close()
            conexion.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@generaciones_bp.route("/generaciones/<int:id_generacion>", methods=["PUT"])
def update_generacion(id_generacion):
    """
    Update generacion
    ---
    parameters:
      - name: id_generacion
        in: path
        type: integer
        required: true
        description: Parámetro id_generacion
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        resultado = GeneracionesService.update(id_generacion, data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@generaciones_bp.route("/generaciones/<int:id_generacion>", methods=["DELETE"])
def delete_generacion(id_generacion):
    """
    Delete generacion
    ---
    parameters:
      - name: id_generacion
        in: path
        type: integer
        required: true
        description: Parámetro id_generacion
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = GeneracionesService.delete(id_generacion)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
