from flask import Blueprint, jsonify, request
from app.services.alumnos_service import AlumnosService
from app.services.grupos_service import GruposService

alumnos_bp = Blueprint("alumnos", __name__)


# Método GET para consultar alumnos
@alumnos_bp.route("/alumnos", methods=["GET"])
def get_alumnos():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        generacion = request.args.get("generacion")
        idGrupo = request.args.get("idGrupo")
        search = request.args.get("search", "").strip()

        resultado = AlumnosService.get_alumnos(page, limit, generacion, idGrupo, search)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@alumnos_bp.route("/alumno/<int:idAlumno>", methods=["GET"])
def get_alumno(idAlumno):
    try:
        resultado = AlumnosService.get_alumno(idAlumno)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#PARA CONSULTAR SOLO UN ALUMNO
@alumnos_bp.route("/<int:idGrupo>/alumnos", methods=["GET"])
def get_alumnos_by_grupo(idGrupo):
    try:
        # Usamos el servicio de grupos que ya hace el JOIN con tb_alumnogrupo
        alumnos = GruposService.get_alumnos_by_grupo(idGrupo)
        return jsonify(alumnos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# bloque para crar a un alumno
@alumnos_bp.route("/crealumnos", methods=["POST"])
def create_alumno():
    try:
        data = request.json
        if not data.get("nombre") or not data.get("apPaterno"):
            return jsonify({"error": "Faltan datos"}), 400

        resultado = AlumnosService.create_alumno(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/importar-alumnos-hoja", methods=["POST"])
def importar_alumnos_hoja():
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
    try:
        resultado = AlumnosService.delete_alumno(id_alumno)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#actualiza solo elumnos y grupos
@alumnos_bp.route("/updateAlumno/<int:id_alumno>", methods=["PUT"])
def update_alumno(id_alumno):
    try:
        data = request.json
        resultado = AlumnosService.update_alumno(id_alumno, data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alumnos_bp.route("/alumnos_by_grupo/<int:idGrupo>", methods=["GET"])
def get_alumnos_grupo(idGrupo):
    try:
        resultado = AlumnosService.get_alumnos_grupo(idGrupo)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alumnos_bp.route("/test_latest_alumno", methods=["GET"])
def test_latest_alumno():
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
    try:
        data = request.json
        if not data.get("idAlumno") or not data.get("idGrupo"):
            return jsonify({"error": "Faltan datos"}), 400
        return jsonify(AlumnosService.create_alumno_grupo(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500