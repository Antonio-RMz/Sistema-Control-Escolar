from flask import Blueprint, jsonify, request
from app.services.alumnos_service import AlumnosService
from app.services.grupos_service import GruposService

alumnos_bp = Blueprint("alumnos", __name__)


# Método GET para consultar alumnos
@alumnos_bp.route("/alumnos", methods=["GET"])
def get_alumnos():
    """
    Get alumnos
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: Parámetro page
      - name: limit
        in: query
        type: string
        required: false
        description: Parámetro limit
      - name: generacion
        in: query
        type: string
        required: false
        description: Parámetro generacion
      - name: idGrupo
        in: query
        type: string
        required: false
        description: Parámetro idGrupo
      - name: search
        in: query
        type: string
        required: false
        description: Parámetro search
      - name: idCentroTrabajo
        in: query
        type: string
        required: false
        description: Parámetro idCentroTrabajo
      - name: id_centro_trabajo
        in: query
        type: string
        required: false
        description: Parámetro id_centro_trabajo
      - name: statusAlumno
        in: query
        type: string
        required: false
        description: Parámetro statusAlumno
      - name: status_alumno
        in: query
        type: string
        required: false
        description: Parámetro status_alumno
      - name: status
        in: query
        type: string
        required: false
        description: Parámetro status
      - name: order
        in: query
        type: string
        required: false
        description: Parámetro order
      - name: orden
        in: query
        type: string
        required: false
        description: Parámetro orden
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        generacion = request.args.get("generacion")
        idGrupo = request.args.get("idGrupo")
        search = request.args.get("search", "").strip()
        id_centro_trabajo = request.args.get("idCentroTrabajo") or request.args.get("id_centro_trabajo")
        status_alumno = request.args.get("statusAlumno") or request.args.get("status_alumno") or request.args.get("status")
        order = request.args.get("order") or request.args.get("orden", "ASC")

        resultado = AlumnosService.get_alumnos(
            page=page, 
            limit=limit, 
            generacion=generacion, 
            idGrupo=idGrupo, 
            search=search,
            id_centro_trabajo=id_centro_trabajo,
            status_alumno=status_alumno,
            order=order
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@alumnos_bp.route("/alumno/<int:idAlumno>", methods=["GET"])
def get_alumno(idAlumno):
    """
    Get alumno
    ---
    parameters:
      - name: idAlumno
        in: path
        type: integer
        required: true
        description: Parámetro idAlumno
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = AlumnosService.get_alumno(idAlumno)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#PARA CONSULTAR SOLO UN ALUMNO
@alumnos_bp.route("/<int:idGrupo>/alumnos", methods=["GET"])
def get_alumnos_by_grupo(idGrupo):
    """
    Get alumnos by grupo
    ---
    parameters:
      - name: idGrupo
        in: path
        type: integer
        required: true
        description: Parámetro idGrupo
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            n_hoja:
              type: string
            id_generacion:
              type: string
            archivo:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        # Usamos el servicio de grupos que ya hace el JOIN con tb_alumnogrupo
        alumnos = GruposService.get_alumnos_by_grupo(idGrupo)
        return jsonify(alumnos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# bloque para crear a un alumno (admite /crealumnos y /alumnos)
@alumnos_bp.route("/crealumnos", methods=["POST"])
@alumnos_bp.route("/alumnos", methods=["POST"])
def create_alumno():
    """
    Create alumno
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            n_hoja:
              type: string
            id_generacion:
              type: string
            archivo:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        resultado, status_code = AlumnosService.create_alumno(data)
        return jsonify(resultado), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/importar-alumnos-hoja", methods=["POST"])
def importar_alumnos_hoja():
    """
    Importar alumnos hoja
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            n_hoja:
              type: string
            id_generacion:
              type: string
            archivo:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json or {}
        # n_hoja es 1-indexed para el usuario (ej: 38 para la hoja 38)
        # internamente restamos 1 para que sea 0-indexed para pandas (37)
        n_hoja = data.get("n_hoja", 38)
        id_gen = data.get("id_generacion", 38)
        archivo = data.get("archivo")  # Opcional

        # Si es un número, restamos 1 para que sea 0-indexed para pandas
        # Si es un string (nombre de la hoja), lo pasamos tal cual
        if isinstance(n_hoja, int) or (isinstance(n_hoja, str) and n_hoja.isdigit()):
            sheet_param = int(n_hoja) - 1
        else:
            sheet_param = n_hoja

        # Preparamos los argumentos para el servicio
        args = [sheet_param, id_gen]
        if archivo:
            # Si el usuario manda un nombre de archivo, lo buscamos en la carpeta scripts
            args.append(f"scripts/{archivo}")

        resultado = AlumnosService.importar_alumnos_hoja(*args)
        return jsonify(resultado), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/deleteAlumno/<int:id_alumno>", methods=["DELETE"])
def delete_alumno(id_alumno):
    """
    Delete alumno
    ---
    parameters:
      - name: id_alumno
        in: path
        type: integer
        required: true
        description: Parámetro id_alumno
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado, status_code = AlumnosService.delete_alumno(id_alumno)
        return jsonify(resultado), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#actualiza solo elumnos y grupos
@alumnos_bp.route("/updateAlumno/<int:id_alumno>", methods=["PUT"])
def update_alumno(id_alumno):
    """
    Update alumno
    ---
    parameters:
      - name: id_alumno
        in: path
        type: integer
        required: true
        description: Parámetro id_alumno
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        resultado = AlumnosService.update_alumno(id_alumno, data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alumnos_bp.route("/alumnos_by_grupo/<int:idGrupo>", methods=["GET"])
def get_alumnos_grupo(idGrupo):
    """
    Get alumnos grupo
    ---
    parameters:
      - name: idGrupo
        in: path
        type: integer
        required: true
        description: Parámetro idGrupo
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        resultado = AlumnosService.get_alumnos_grupo(idGrupo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/test_latest_alumno", methods=["GET"])
def test_latest_alumno():
    """
    Test latest alumno
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: Parámetro page
      - name: limit
        in: query
        type: string
        required: false
        description: Parámetro limit
      - name: search
        in: query
        type: string
        required: false
        description: Parámetro search
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    from app.config.conexion import get_connection
    import pymysql
    conexion = get_connection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT idAlumno, nombre, apPaterno, curp, folioCertificado, fechaRecogioCertificado, recogioCertificado
            FROM tb_alumnos
            ORDER BY idAlumno DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            for k, v in list(row.items()):
                if not isinstance(v, (str, int, float)) and v is not None:
                    row[k] = str(v)
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()


@alumnos_bp.route("/getAlumnoEquivalencia", methods=["GET"])
def get_alumno_equivalencia():
    """
    Get alumno equivalencia
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: Parámetro page
      - name: limit
        in: query
        type: string
        required: false
        description: Parámetro limit
      - name: search
        in: query
        type: string
        required: false
        description: Parámetro search
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            idAlumno:
              type: string
            idGrupo:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        search = request.args.get("search", "").strip()

        resultado = AlumnosService.get_alumno_equivalencia(page, limit, search)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/createAlumnoGrupo", methods=["POST"])
def create_alumno_grupo():
    """
    Create alumno grupo
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            idAlumno:
              type: string
            idGrupo:
              type: string
    responses:
      200:
        description: Operación exitosa
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json
        if not data.get("idAlumno") or not data.get("idGrupo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(AlumnosService.create_alumno_grupo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500