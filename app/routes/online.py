"""Endpoints de la modalidad online BGNE (78 semanas según las fechas del grupo, cola FIFO de pagos y Moodle)."""
from flask import Blueprint, jsonify, request

from app.services.online_service import OnlineError, OnlineService
from app.utils.seguridad import auditar, error_interno, usuario_solicitante

online_bp = Blueprint("online", __name__)


def _responder(fn, *args, contexto="online", **kwargs):
    try:
        resultado, status = fn(*args, **kwargs)
        return jsonify(resultado), status
    except OnlineError as e:
        return jsonify({"success": False, "message": str(e)}), e.status
    except Exception as e:
        return error_interno(e, contexto)


# ------------------------------------------------------------------ alumnos

@online_bp.route("/online/alumnos", methods=["GET"])
def listar_alumnos():
    """Alumnos online con su semana de calendario, semanas pagadas y semáforo de atraso."""
    return _responder(OnlineService.listar_alumnos, (request.args.get("search") or "").strip())


@online_bp.route("/online/alumnos/<int:id_alumno>", methods=["GET"])
def detalle_alumno(id_alumno):
    """Estado del alumno, sus 78 semanas e historial de pagos."""
    return _responder(OnlineService.detalle_alumno, id_alumno)


@online_bp.route("/online/alumnos/<int:id_alumno>/pagos/vista-previa", methods=["GET"])
def vista_previa_pago(id_alumno):
    """Qué semanas cubriría un pago de N semanas, cuáles se habilitan hoy y sus fechas límite."""
    return _responder(OnlineService.vista_previa_pago, id_alumno,
                      request.args.get("semanas", 1), request.args.get("fecha_pago"))


@online_bp.route("/online/alumnos/<int:id_alumno>/pagos", methods=["POST"])
def registrar_pago(id_alumno):
    """Registra un pago de N semanas (cola FIFO) y habilita en Moodle las que ya llegaron."""
    data = request.get_json(silent=True) or {}
    auditar("online_pago", id_alumno=id_alumno, semanas=data.get("semanas"), monto=data.get("monto"))
    return _responder(OnlineService.registrar_pago, id_alumno, data, usuario_solicitante())


@online_bp.route("/online/alumnos/<int:id_alumno>/integracion", methods=["GET"])
def vista_integracion(id_alumno):
    """Si hoy se puede pasar a online según las fechas de su grupo BGNE, y en qué trimestre iniciaría."""
    return _responder(OnlineService.vista_integracion, id_alumno)


@online_bp.route("/online/alumnos/<int:id_alumno>/modalidad-online", methods=["POST"])
def cambiar_modalidad_online(id_alumno):
    """Pasa al alumno a online en su mismo grupo (solo al concluir el trimestre en curso) y crea su cuenta de Moodle."""
    data = request.get_json(silent=True) or {}
    auditar("online_alta", id_alumno=id_alumno, dia_pago=data.get("dia_pago"))
    return _responder(OnlineService.cambiar_modalidad_online, id_alumno, data)


@online_bp.route("/online/alumnos/<int:id_alumno>/moodle/sincronizar", methods=["POST"])
def sincronizar_moodle(id_alumno):
    return _responder(OnlineService.sincronizar_moodle, id_alumno)


@online_bp.route("/online/alumnos/<int:id_alumno>/moodle/suspension", methods=["POST"])
def suspension_moodle(id_alumno):
    """Suspensión o reactivación MANUAL de la cuenta de Moodle (no hay suspensiones automáticas)."""
    data = request.get_json(silent=True) or {}
    suspender = str(data.get("accion", "suspender")).lower() != "reactivar"
    auditar("online_suspension_manual", id_alumno=id_alumno, suspender=suspender)
    return _responder(OnlineService.suspension_manual, id_alumno, suspender)


# ------------------------------------------------------------------ proceso de habilitación

@online_bp.route("/online/habilitar-semanas", methods=["POST"])
def habilitar_semanas():
    """Ejecuta a mano el proceso de los sábados 07:00 (habilita semanas adelantadas y reintenta Moodle)."""
    auditar("online_habilitar_manual")
    return _responder(OnlineService.habilitar_pendientes)


# ------------------------------------------------------------------ configuración

@online_bp.route("/online/planes", methods=["GET"])
def listar_planes():
    return _responder(OnlineService.listar_planes)


@online_bp.route("/online/planes/<int:id_plan>/bloques", methods=["PUT"])
def actualizar_bloques(id_plan):
    data = request.get_json(silent=True) or {}
    auditar("online_bloques", id_plan=id_plan, bloques=data.get("bloques"))
    return _responder(OnlineService.actualizar_bloques, id_plan, data.get("bloques"))


@online_bp.route("/online/cursos/<int:id_curso>", methods=["PUT"])
def actualizar_curso(id_curso):
    data = request.get_json(silent=True) or {}
    auditar("online_curso", id_curso=id_curso, **{k: data.get(k) for k in ("moodle_course_id", "nombre") if k in data})
    return _responder(OnlineService.actualizar_curso, id_curso, data)


@online_bp.route("/online/cursos/<int:id_curso>/preparar-grupos", methods=["POST"])
def preparar_grupos(id_curso):
    return _responder(OnlineService.preparar_grupos_curso, id_curso)


@online_bp.route("/online/grupos", methods=["GET"])
def listar_grupos():
    """Grupos BGNE activos con su calendario (inicio de cada trimestre, semana actual y ventana de cambio a online)."""
    return _responder(OnlineService.listar_grupos)


@online_bp.route("/online/grupos/<int:id_grupo>/plan", methods=["PUT"])
def asignar_plan_grupo(id_grupo):
    data = request.get_json(silent=True) or {}
    auditar("online_plan_grupo", id_grupo=id_grupo, id_plan=data.get("id_plan"))
    return _responder(OnlineService.asignar_plan_grupo, id_grupo, data.get("id_plan"))
