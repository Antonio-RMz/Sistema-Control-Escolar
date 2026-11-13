"""
Historial de cambios de alumnos (línea del tiempo en el listado de alumnos).
Tabla: tb_alumnos_historial (id, id_alumno, tipo, titulo, cambios JSON, usuario, usuario_id, created_at).
"""
import json

from flask import Blueprint, jsonify, request

from app.config.conexion import get_connection
from app.utils.seguridad import error_interno

historial_alumnos_bp = Blueprint("historial_alumnos", __name__)

_TIPOS = ("ALTA", "GRUPO", "ESTATUS", "MODALIDAD", "PERFIL")


def _iso(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else (str(valor) if valor else None)


@historial_alumnos_bp.route("/alumnos/<int:id_alumno>/historial", methods=["GET"])
def listar_historial(id_alumno):
    """
    Eventos del alumno, más recientes primero. Si no hay registro de alta se arma con createAt/createBy.
    ---
    parameters:
      - {name: id_alumno, in: path, type: integer, required: true}
    responses:
      200: {description: "data: [{tipo, titulo, cambios, usuario, fecha}]"}
    """
    conexion = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT tipo, titulo, cambios, usuario, created_at FROM tb_alumnos_historial "
            "WHERE id_alumno = %s ORDER BY created_at DESC, id DESC",
            (id_alumno,),
        )
        eventos = []
        for f in cursor.fetchall():
            cambios = f["cambios"]
            if isinstance(cambios, (str, bytes)):
                try:
                    cambios = json.loads(cambios)
                except ValueError:
                    cambios = []
            eventos.append({
                "tipo": f["tipo"], "titulo": f["titulo"], "cambios": cambios or [],
                "usuario": f["usuario"], "fecha": _iso(f["created_at"]),
            })

        if not any(e["tipo"] == "ALTA" for e in eventos):
            cursor.execute("SELECT createAt, createBy FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))
            a = cursor.fetchone()
            if a and a["createAt"]:
                eventos.append({"tipo": "ALTA", "titulo": "Alta del alumno", "cambios": [], "usuario": a["createBy"], "fecha": _iso(a["createAt"])})

        cursor.close()
        return jsonify({"success": True, "data": eventos})
    except Exception as e:
        return error_interno(e, "listar historial alumno")
    finally:
        if conexion:
            conexion.close()


@historial_alumnos_bp.route("/alumnos/<int:id_alumno>/historial", methods=["POST"])
def registrar_evento(id_alumno):
    """
    Registrar un evento del historial
    ---
    parameters:
      - {name: id_alumno, in: path, type: integer, required: true}
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            tipo: {type: string, enum: [ALTA, GRUPO, ESTATUS, MODALIDAD, PERFIL]}
            titulo: {type: string}
            cambios: {type: array, items: {type: object}}
            usuario: {type: string}
            usuario_id: {type: string}
    responses:
      201: {description: Registrado}
      400: {description: Datos inválidos}
    """
    conexion = None
    try:
        data = request.json or {}
        tipo = data.get("tipo")
        titulo = (data.get("titulo") or "").strip()
        if tipo not in _TIPOS or not titulo:
            return jsonify({"error": "tipo o titulo inválido"}), 400
        cambios = data.get("cambios") or []
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO tb_alumnos_historial (id_alumno, tipo, titulo, cambios, usuario, usuario_id, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (id_alumno, tipo, titulo[:120], json.dumps(cambios, ensure_ascii=False) if cambios else None,
             (data.get("usuario") or None), (str(data.get("usuario_id")) if data.get("usuario_id") else None)),
        )
        conexion.commit()
        cursor.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return error_interno(e, "registrar historial alumno")
    finally:
        if conexion:
            conexion.close()
