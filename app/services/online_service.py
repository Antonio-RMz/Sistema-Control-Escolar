"""
Modalidad online BGNE: 78 semanas (6 trimestres x 13), calendario del GRUPO del alumno, cola FIFO de pagos.

Reglas:
  - Solo aplica a grupos BGNE (id_centroTrabajo = 3). Un grupo puede ser mixto: el alumno se queda en su grupo y
    lo que cambia es tb_alumnos.modalidad_estudio (PRESENCIAL / ONLINE).
  - Fuente única de fechas: tb_grupos.fechaInicio. El trimestre N inicia en fechaInicio + 13 * (N - 1) semanas
    (misma regla que PeriodoAcademicoService). Las semanas del calendario inician en sábado: para grupos de domingo
    la semana empieza el sábado anterior a la clase.
  - El alumno entra a online en el inicio de un trimestre (semana_inicio_online = (T - 1) * 13 + 1). Solo se permite
    cuando el trimestre en curso del grupo ya concluyó (después de su última clase) o durante la primera semana
    del trimestre que inicia.
  - Cada semana pagada se asigna a la semana pendiente más antigua (FIFO); las pagadas son consecutivas desde
    semana_inicio_online. Se habilita en cuanto su fecha de inicio llegó; si se pagó por adelantado queda EN_ESPERA
    y la habilita el proceso de los sábados 07:00.
  - Fecha límite de entrega: 6 días naturales desde el desbloqueo, 23:59:59 (desde la fecha de pago o, si se pagó
    por adelantado, desde el día de cobro del alumno en esa semana: sábado → viernes, domingo → sábado).
  - Semáforo (sin bajas ni suspensiones automáticas): semanas cuyo día de cobro ya pasó menos semanas pagadas.
    0 verde, 1 amarillo (baja), 2 naranja (preventiva), 3 o más rojo (máxima).
"""
import datetime
import secrets

from app.config.conexion import get_connection
from app.services.alumnos_service import get_mexico_now
from app.services.moodle_service import MoodleService

CCT_BGNE = 3
SEMANAS_TRIMESTRE = 13
TOTAL_SEMANAS = 78
DIAS_COBRO = ("SABADO", "DOMINGO")
METODOS_PAGO = ("EFECTIVO", "TRANSFERENCIA", "DEPOSITO", "TARJETA")
SEMAFORO = [
    (0, "VERDE", "Al corriente"),
    (1, "AMARILLO", "Alerta baja"),
    (2, "NARANJA", "Alerta preventiva"),
    (3, "ROJO", "Alerta máxima"),
]


class OnlineError(Exception):
    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.status = status


# ---------------------------------------------------------------------------- utilidades

def hoy():
    return get_mexico_now().date()


def ahora():
    return get_mexico_now().replace(tzinfo=None, microsecond=0)


def _fecha(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _iso(v):
    return v.isoformat(sep=" ") if isinstance(v, datetime.datetime) else (v.isoformat() if isinstance(v, datetime.date) else v)


def dia_cobro(al):
    d = str(al.get("dia_pago") or "SABADO").upper()
    return d if d in DIAS_COBRO else "SABADO"


def offset_cobro(al):
    """Días desde el sábado de inicio de semana hasta el día de cobro del alumno."""
    return 1 if dia_cobro(al) == "DOMINGO" else 0


def semana_inicio_alumno(al):
    s = al.get("semana_inicio_online")
    if s:
        return int(s)
    t = max(1, min(6, int(al.get("trimestre_inicio_online") or 1)))
    return (t - 1) * SEMANAS_TRIMESTRE + 1


def semaforo(atraso):
    nivel = min(3, max(0, int(atraso)))
    _, color, texto = SEMAFORO[nivel]
    return {"nivel": nivel, "color": color, "texto": texto}


def generar_folio():
    return f"ONL-{hoy():%Y%m%d}-{secrets.token_hex(3).upper()}"


# ---------------------------------------------------------------------------- plan de bloques

def plan_base_id(cur):
    cur.execute("SELECT id FROM tb_online_planes WHERE activo = 1 ORDER BY id LIMIT 1")
    r = cur.fetchone()
    return r["id"] if r else None


def cargar_plan(cur, id_plan):
    cur.execute("SELECT * FROM tb_online_planes WHERE id = %s", (id_plan,))
    plan = cur.fetchone()
    if not plan:
        raise OnlineError("El plan de bloques online no existe.", 404)
    cur.execute("SELECT * FROM tb_online_plan_bloques WHERE id_plan = %s ORDER BY trimestre, bloque", (id_plan,))
    bloques = cur.fetchall()
    ids = [b["id"] for b in bloques] or [0]
    cur.execute(f"SELECT * FROM tb_online_bloque_cursos WHERE id_plan_bloque IN ({','.join(['%s'] * len(ids))}) ORDER BY id_plan_bloque, orden", ids)
    cursos = cur.fetchall()
    ids_c = [c["id"] for c in cursos] or [0]
    cur.execute(f"""
        SELECT cm.id_bloque_curso, m.id, m.nombreMateria
        FROM tb_online_curso_materias cm JOIN tb_materias m ON m.id = cm.id_materia
        WHERE cm.id_bloque_curso IN ({','.join(['%s'] * len(ids_c))}) ORDER BY m.id
    """, ids_c)
    materias = cur.fetchall()
    for c in cursos:
        c["materias"] = [{"id": m["id"], "nombre": (m["nombreMateria"] or "").strip()} for m in materias if m["id_bloque_curso"] == c["id"]]
    for b in bloques:
        b["cursos"] = [c for c in cursos if c["id_plan_bloque"] == b["id"]]
    plan["bloques"] = bloques
    plan["errores"] = validar_bloques(bloques)
    plan["mapa"] = mapa_semanas(bloques) if not plan["errores"] else None
    return plan


def validar_bloques(bloques):
    errores = []
    for t in range(1, 7):
        del_t = [b for b in bloques if int(b["trimestre"]) == t]
        if len(del_t) != 3:
            errores.append(f"El trimestre {t} debe tener 3 bloques (tiene {len(del_t)}).")
            continue
        suma = sum(int(b["semanas"]) for b in del_t)
        if suma != SEMANAS_TRIMESTRE:
            errores.append(f"Los bloques del trimestre {t} suman {suma} semanas; deben sumar {SEMANAS_TRIMESTRE}.")
    return errores


def mapa_semanas(bloques):
    """Lista de 78 posiciones: semana global → trimestre, bloque y semana dentro del bloque."""
    mapa = []
    for b in sorted(bloques, key=lambda x: (int(x["trimestre"]), int(x["bloque"]))):
        for s in range(1, int(b["semanas"]) + 1):
            mapa.append({"semana": len(mapa) + 1, "trimestre": int(b["trimestre"]), "bloque": int(b["bloque"]),
                         "semana_bloque": s, "id_plan_bloque": b["id"]})
    return mapa


# ---------------------------------------------------------------------------- calendario del grupo

def preparar_grupo(g, id_plan_base):
    """Agrega al registro de tb_grupos los datos de calendario online."""
    fi = _fecha(g.get("fechaInicio"))
    g["es_bgne"] = int(g.get("id_centroTrabajo") or 0) == CCT_BGNE
    g["fecha_clase"] = fi
    # Sábado en que inicia la semana 1 (para grupos de domingo, el sábado anterior)
    g["fecha_inicio"] = fi - datetime.timedelta(days=(fi.weekday() - 5) % 7) if fi else None
    g["dia_clase"] = "DOMINGO" if fi and fi.weekday() == 6 else "SABADO"
    g["id_plan"] = g.get("id_plan_online") or id_plan_base
    return g


def problema_calendario(grupo):
    if not grupo:
        return "El alumno no tiene grupo asignado"
    if not grupo["es_bgne"]:
        return f"El grupo {grupo['clave']} no es BGNE (la modalidad online solo aplica a BGNE)"
    if not grupo["fecha_inicio"]:
        return f"El grupo {grupo['clave']} no tiene fecha de inicio"
    if not grupo["id_plan"]:
        return "No hay plan de bloques online configurado"
    return None


def inicio_semana(grupo, g):
    return grupo["fecha_inicio"] + datetime.timedelta(days=7 * (int(g) - 1))


def semana_calendario(grupo, fecha):
    return (fecha - grupo["fecha_inicio"]).days // 7 + 1


def clase_inicio_trimestre(grupo, t):
    return grupo["fecha_clase"] + datetime.timedelta(weeks=SEMANAS_TRIMESTRE * (t - 1))


def clase_fin_trimestre(grupo, t):
    """Última clase del trimestre (misma regla que PeriodoAcademicoService: inicio + 12 semanas)."""
    return clase_inicio_trimestre(grupo, t) + datetime.timedelta(weeks=SEMANAS_TRIMESTRE - 1)


def fecha_limite(fecha_pago, grupo, g, al):
    """6 días naturales desde el desbloqueo (pago, o día de cobro si se pagó por adelantado), a las 23:59:59."""
    base = max(_fecha(fecha_pago), inicio_semana(grupo, g) + datetime.timedelta(days=offset_cobro(al)))
    return datetime.datetime.combine(base + datetime.timedelta(days=6), datetime.time(23, 59, 59))


def ventana_cambio(grupo, f=None):
    """
    ¿Se puede pasar hoy a online? Solo al concluir el trimestre en curso del grupo (después de su última clase)
    o durante la primera semana del trimestre que inicia. Regresa {permitido, trimestre, semana_inicio, inicio, mensaje}.
    """
    f = f or hoy()
    err = problema_calendario(grupo)
    if err:
        return {"permitido": False, "mensaje": err + "."}
    g = semana_calendario(grupo, f)
    if g > TOTAL_SEMANAS:
        return {"permitido": False, "mensaje": f"El grupo {grupo['clave']} ya concluyó sus 6 trimestres."}

    def ok(t, nota):
        return {"permitido": True, "trimestre": t, "semana_inicio": (t - 1) * SEMANAS_TRIMESTRE + 1,
                "inicio": _iso(clase_inicio_trimestre(grupo, t)), "mensaje": nota}

    if g < 1:
        return ok(1, f"El grupo aún no inicia; empezará en online el 1° trimestre el {clase_inicio_trimestre(grupo, 1):%d/%m/%Y}.")
    t_cur = (g - 1) // SEMANAS_TRIMESTRE + 1
    sem_t = (g - 1) % SEMANAS_TRIMESTRE + 1
    if sem_t == 1:
        return ok(t_cur, f"El {t_cur}° trimestre del grupo inició el {clase_inicio_trimestre(grupo, t_cur):%d/%m/%Y}; empieza desde su semana 1.")
    fin = clase_fin_trimestre(grupo, t_cur)
    if f > fin:
        if t_cur >= 6:
            return {"permitido": False, "mensaje": f"El grupo {grupo['clave']} concluyó el 6° trimestre."}
        return ok(t_cur + 1, f"El {t_cur}° trimestre concluyó el {fin:%d/%m/%Y}; empezará el {t_cur + 1}° trimestre el {clase_inicio_trimestre(grupo, t_cur + 1):%d/%m/%Y}.")
    if t_cur >= 6:
        return {"permitido": False, "mensaje": f"El grupo {grupo['clave']} cursa su último trimestre (semana {sem_t} de 13); ya no hay un trimestre siguiente para iniciar en online."}
    return {"permitido": False,
            "mensaje": f"El grupo {grupo['clave']} cursa el {t_cur}° trimestre (semana {sem_t} de 13), que concluye el {fin:%d/%m/%Y}. "
                       f"El cambio a online se permite a partir del {fin + datetime.timedelta(days=1):%d/%m/%Y} para iniciar el "
                       f"{t_cur + 1}° trimestre el {clase_inicio_trimestre(grupo, t_cur + 1):%d/%m/%Y}."}


class _Contexto:
    """Cache de grupos y planes durante una operación."""

    def __init__(self, cur):
        self.cur = cur
        self.grupos = {}
        self.planes = {}
        self.base = plan_base_id(cur)

    def grupo(self, id_grupo):
        if not id_grupo:
            return None
        if id_grupo not in self.grupos:
            self.cur.execute("""
                SELECT id, clave, fechaInicio, fechaFin, id_centroTrabajo, modalidadHorario, id_nivel_academico,
                       statusGrupo, id_plan_online
                FROM tb_grupos WHERE id = %s
            """, (id_grupo,))
            g = self.cur.fetchone()
            self.grupos[id_grupo] = preparar_grupo(g, self.base) if g else None
        return self.grupos[id_grupo]

    def plan(self, id_plan):
        if not id_plan:
            return None
        if id_plan not in self.planes:
            self.planes[id_plan] = cargar_plan(self.cur, id_plan)
        return self.planes[id_plan]

    def calendario(self, al):
        """(grupo, plan, problema) del alumno."""
        grupo = self.grupo(al.get("idGrupo"))
        err = problema_calendario(grupo)
        if err:
            return grupo, None, err
        plan = self.plan(grupo["id_plan"])
        if not plan["mapa"]:
            return grupo, plan, "El plan de bloques está incompleto: " + " ".join(plan["errores"])
        return grupo, plan, None


# ---------------------------------------------------------------------------- estado del alumno

def calcular_estado(al, grupo, plan, pagadas, problema=None, f=None):
    """Situación del alumno en el calendario de su grupo. `pagadas` = número de semanas pagadas."""
    f = f or hoy()
    ini = semana_inicio_alumno(al)
    pagadas = int(pagadas or 0)
    est = {
        "semana_inicio": ini,
        "trimestre_inicio": (ini - 1) // SEMANAS_TRIMESTRE + 1,
        "semanas_pagadas": pagadas,
        "ultima_semana_pagada": ini + pagadas - 1 if pagadas else None,
        "dia_pago": dia_cobro(al),
        "configurado": problema is None and bool(grupo and plan and plan.get("mapa")),
    }
    if not est["configurado"]:
        est.update({"semana_calendario": None, "ubicacion": None, "semanas_vencidas": 0, "atraso": 0,
                    "semaforo": semaforo(0), "siguiente_semana": None, "fecha_proximo_pago": None,
                    "aviso": problema or "Calendario no disponible"})
        return est

    off = offset_cobro(al)
    g_hoy = semana_calendario(grupo, f)
    # Última semana cuyo día de cobro ya pasó (se debe a partir del día siguiente al cobro)
    g_due = g_hoy if f > inicio_semana(grupo, g_hoy) + datetime.timedelta(days=off) else g_hoy - 1
    vencidas = max(0, min(TOTAL_SEMANAS, g_due) - ini + 1)
    atraso = max(0, vencidas - pagadas)
    siguiente = ini + pagadas if ini + pagadas <= TOTAL_SEMANAS else None
    ubic = plan["mapa"][g_hoy - 1] if 1 <= g_hoy <= TOTAL_SEMANAS else None
    est.update({
        "semana_calendario": g_hoy,
        "ubicacion": ubic and {k: ubic[k] for k in ("trimestre", "bloque", "semana_bloque")},
        "semanas_vencidas": vencidas,
        "atraso": atraso,
        "semaforo": semaforo(atraso),
        "siguiente_semana": siguiente,
        "fecha_proximo_pago": _iso(inicio_semana(grupo, siguiente) + datetime.timedelta(days=off)) if siguiente else None,
        "aviso": "Concluyó las 78 semanas" if siguiente is None else ("El grupo aún no inicia" if g_hoy < 1 else None),
    })
    return est


def _alumno(cur, id_alumno, bloquear=False):
    cur.execute(f"""
        SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl, a.correoAlumno, a.celularAlumno,
               a.statusAlumno, a.modalidad_estudio, a.dia_pago, a.idGrupo, a.moodle_user_id, a.moodle_username,
               a.trimestre_inicio_online, a.semana_inicio_online
        FROM tb_alumnos a WHERE a.idAlumno = %s {'FOR UPDATE' if bloquear else ''}
    """, (id_alumno,))
    al = cur.fetchone()
    if not al:
        raise OnlineError("Alumno no encontrado.", 404)
    return al


def _contar_pagadas(cur, id_alumno):
    cur.execute("SELECT COUNT(*) AS n FROM tb_alumno_semanas_online WHERE id_alumno = %s", (id_alumno,))
    return int(cur.fetchone()["n"])


def _actualizar_resumen_alumno(cur, al, grupo, plan):
    """Mantiene las columnas de resumen que leen otras pantallas."""
    est = calcular_estado(al, grupo, plan, _contar_pagadas(cur, al["idAlumno"]))
    cur.execute("""
        UPDATE tb_alumnos SET semanas_totales_pagadas = %s, semana_actual_pagada = %s, fecha_proximo_pago = %s
        WHERE idAlumno = %s
    """, (est["semanas_pagadas"], est["ultima_semana_pagada"] or 0, est["fecha_proximo_pago"], al["idAlumno"]))
    return est


def _nombre(al):
    return " ".join(x for x in [al.get("nombre"), al.get("apPaterno"), al.get("apMaterno")] if x).strip()


# ---------------------------------------------------------------------------- Moodle del alumno

def username_moodle(al):
    nc = (al.get("numeroControl") or "").strip().lower()
    return nc or f"alu{al['idAlumno']}"


def asegurar_usuario_moodle(cur, al, password=None):
    """Crea (o encuentra) la cuenta de Moodle del alumno y la guarda. Regresa (moodle_user_id, error)."""
    if al.get("moodle_user_id"):
        return int(al["moodle_user_id"]), None
    username = (al.get("moodle_username") or username_moodle(al)).lower()
    password = (password or "").strip() or f"Bti.{username}*"
    res = MoodleService.crear_usuario(username, password, al.get("nombre"),
                                      f"{al.get('apPaterno') or ''} {al.get('apMaterno') or ''}".strip(), al.get("correoAlumno"))
    if res.get("success"):
        cur.execute("UPDATE tb_alumnos SET moodle_user_id = %s, moodle_username = %s WHERE idAlumno = %s",
                    (res["moodle_user_id"], username, al["idAlumno"]))
        if res.get("is_new"):
            cur.execute("UPDATE tb_alumnos SET moodle_password = %s WHERE idAlumno = %s", (password, al["idAlumno"]))
        al["moodle_user_id"], al["moodle_username"] = res["moodle_user_id"], username
        return int(res["moodle_user_id"]), None
    return None, str(res.get("error") or "No se pudo crear la cuenta de Moodle.")[:250]


def _sincronizar_moodle(con, cur, al, plan):
    """Aplica en Moodle las semanas HABILITADAS que aún no se sincronizan. Regresa lista de errores."""
    cur.execute("""
        SELECT id, semana_global FROM tb_alumno_semanas_online
        WHERE id_alumno = %s AND estatus = 'HABILITADA' AND moodle_sincronizado = 0 ORDER BY semana_global
    """, (al["idAlumno"],))
    filas = cur.fetchall()
    if not filas:
        return []

    user_id, err_user = asegurar_usuario_moodle(cur, al)
    errores = []
    # Una llamada por bloque: basta la semana más alta del bloque (los grupos de Moodle son acumulativos)
    por_bloque = {}
    for fila in filas:
        pos = plan["mapa"][int(fila["semana_global"]) - 1]
        por_bloque.setdefault(pos["id_plan_bloque"], []).append((fila, pos))

    for id_bloque, items in por_bloque.items():
        semana_max = max(p["semana_bloque"] for _, p in items)
        bloque = next(b for b in plan["bloques"] if b["id"] == id_bloque)
        error = err_user
        if not error and not bloque["cursos"]:
            error = f"El bloque {bloque['bloque']} del trimestre {bloque['trimestre']} no tiene cursos configurados."
        if not error:
            for curso in bloque["cursos"]:
                if not curso.get("moodle_course_id"):
                    error = f"El curso «{curso['nombre']}» no tiene ID de Moodle."
                    break
                ok, e = MoodleService.habilitar_semana_en_curso(user_id, int(curso["moodle_course_id"]), semana_max)
                if not ok:
                    error = f"{curso['nombre']}: {e}"
                    break
        ids = [f["id"] for f, _ in items]
        marcas = ",".join(["%s"] * len(ids))
        if error:
            cur.execute(f"UPDATE tb_alumno_semanas_online SET moodle_error = %s WHERE id IN ({marcas})", [str(error)[:255], *ids])
            errores.append(str(error))
        else:
            cur.execute(f"UPDATE tb_alumno_semanas_online SET moodle_sincronizado = 1, moodle_error = NULL WHERE id IN ({marcas})", ids)
        con.commit()
    return errores


def habilitar_alumno(con, cur, id_alumno, ctx=None):
    """Habilita las semanas pagadas cuya fecha ya llegó y las aplica en Moodle. Regresa resumen."""
    ctx = ctx or _Contexto(cur)
    al = _alumno(cur, id_alumno)
    grupo, plan, problema = ctx.calendario(al)
    if problema:
        return {"idAlumno": id_alumno, "habilitadas": [], "errores_moodle": [problema + "."]}

    f = hoy()
    cur.execute("""
        SELECT id, semana_global, fecha_pago FROM tb_alumno_semanas_online
        WHERE id_alumno = %s AND estatus = 'EN_ESPERA' ORDER BY semana_global
    """, (id_alumno,))
    habilitadas = []
    for fila in cur.fetchall():
        g = int(fila["semana_global"])
        if inicio_semana(grupo, g) > f:
            break
        limite = fecha_limite(fila["fecha_pago"], grupo, g, al)
        cur.execute("""
            UPDATE tb_alumno_semanas_online
            SET estatus = 'HABILITADA', fecha_habilitada = %s, fecha_limite = %s, fecha_limite_original = %s
            WHERE id = %s AND estatus = 'EN_ESPERA'
        """, (ahora(), limite, limite, fila["id"]))
        habilitadas.append(g)
    con.commit()
    errores = _sincronizar_moodle(con, cur, al, plan)
    return {"idAlumno": id_alumno, "habilitadas": habilitadas, "errores_moodle": errores}


# ---------------------------------------------------------------------------- servicio público

class OnlineService:

    # -------------------------------------------------------------- alumnos

    @staticmethod
    def listar_alumnos(search=""):
        con = get_connection()
        cur = con.cursor()
        try:
            where, vals = ["a.modalidad_estudio = 'ONLINE'"], []
            if search:
                where.append("(CONCAT_WS(' ', a.nombre, a.apPaterno, a.apMaterno) LIKE %s OR a.numeroControl LIKE %s)")
                vals += [f"%{search}%", f"%{search}%"]
            cur.execute(f"""
                SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl, a.correoAlumno, a.celularAlumno,
                       a.statusAlumno, a.dia_pago, a.moodle_user_id, a.moodle_username, a.trimestre_inicio_online,
                       a.semana_inicio_online, a.idGrupo,
                       (SELECT COUNT(*) FROM tb_alumno_semanas_online s WHERE s.id_alumno = a.idAlumno) AS pagadas,
                       (SELECT COUNT(*) FROM tb_alumno_semanas_online s WHERE s.id_alumno = a.idAlumno AND s.estatus = 'EN_ESPERA') AS en_espera,
                       (SELECT COUNT(*) FROM tb_alumno_semanas_online s WHERE s.id_alumno = a.idAlumno AND s.estatus = 'HABILITADA' AND s.moodle_sincronizado = 0) AS sin_sincronizar
                FROM tb_alumnos a
                WHERE {' AND '.join(where)}
                ORDER BY a.apPaterno, a.apMaterno, a.nombre
            """, vals)
            filas = cur.fetchall()
            ctx = _Contexto(cur)
            salida = []
            for al in filas:
                grupo, plan, problema = ctx.calendario(al)
                est = calcular_estado(al, grupo, plan, al["pagadas"], problema)
                est["en_espera"] = int(al["en_espera"])
                est["sin_sincronizar"] = int(al["sin_sincronizar"])
                salida.append({
                    "idAlumno": al["idAlumno"],
                    "nombreCompleto": _nombre(al),
                    "nombre": al["nombre"],
                    "numeroControl": al["numeroControl"],
                    "correoAlumno": al["correoAlumno"],
                    "celularAlumno": al["celularAlumno"],
                    "statusAlumno": al["statusAlumno"],
                    "moodle_username": al["moodle_username"],
                    "tiene_moodle": bool(al["moodle_user_id"]),
                    "idGrupo": al["idGrupo"],
                    "grupo": grupo["clave"] if grupo else None,
                    "grupo_inicio": _iso(grupo["fecha_clase"]) if grupo else None,
                    "estado": est,
                })
            return {"success": True, "alumnos": salida}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def detalle_alumno(id_alumno):
        con = get_connection()
        cur = con.cursor()
        try:
            al = _alumno(cur, id_alumno)
            ctx = _Contexto(cur)
            grupo, plan, problema = ctx.calendario(al)
            cur.execute("SELECT * FROM tb_alumno_semanas_online WHERE id_alumno = %s ORDER BY semana_global", (id_alumno,))
            filas = {int(r["semana_global"]): r for r in cur.fetchall()}
            est = calcular_estado(al, grupo, plan, len(filas), problema)

            semanas = []
            if est["configurado"]:
                f = hoy()
                off = offset_cobro(al)
                for pos in plan["mapa"]:
                    g = pos["semana"]
                    ini = inicio_semana(grupo, g)
                    r = filas.get(g)
                    if g < est["semana_inicio"]:
                        estado = "NO_APLICA"
                    elif r:
                        estado = r["estatus"]
                    elif f > ini + datetime.timedelta(days=off):
                        estado = "ADEUDO"
                    else:
                        estado = "PENDIENTE"
                    semanas.append({
                        **pos, "inicio": _iso(ini), "estado": estado,
                        "fecha_pago": _iso(r["fecha_pago"]) if r else None,
                        "fecha_habilitada": _iso(r["fecha_habilitada"]) if r else None,
                        "fecha_limite": _iso(r["fecha_limite"]) if r else None,
                        "moodle_sincronizado": bool(r["moodle_sincronizado"]) if r else None,
                        "moodle_error": r["moodle_error"] if r else None,
                    })

            cur.execute("""
                SELECT id, fecha_pago, folio_ticket, semana_desde, semana_hasta, semanas_pagadas, monto, metodo_pago,
                       observaciones, registrado_por, created_at
                FROM tb_alumno_pagos WHERE id_alumno = %s ORDER BY created_at DESC, id DESC
            """, (id_alumno,))
            pagos = [{k: (_iso(v) if isinstance(v, (datetime.date, datetime.datetime)) else (float(v) if k == "monto" and v is not None else v))
                      for k, v in p.items()} for p in cur.fetchall()]

            return {
                "success": True,
                "alumno": {
                    "idAlumno": al["idAlumno"], "nombreCompleto": _nombre(al), "numeroControl": al["numeroControl"],
                    "moodle_username": al["moodle_username"], "tiene_moodle": bool(al["moodle_user_id"]),
                    "dia_pago": dia_cobro(al),
                },
                "grupo": grupo and {"id": grupo["id"], "clave": grupo["clave"], "fecha_inicio": _iso(grupo["fecha_clase"]),
                                    "dia_clase": grupo["dia_clase"]},
                "plan_bloques": plan and [{"id": b["id"], "trimestre": b["trimestre"], "bloque": b["bloque"], "semanas": b["semanas"],
                                           "cursos": [c["nombre"] for c in b["cursos"]]} for b in plan["bloques"]],
                "estado": est,
                "semanas": semanas,
                "pagos": pagos,
            }, 200
        finally:
            cur.close()
            con.close()

    # -------------------------------------------------------------- pagos

    @staticmethod
    def _semanas_de_pago(al, grupo, plan, pagadas, n, fecha_pago):
        desde = semana_inicio_alumno(al) + pagadas
        restantes = TOTAL_SEMANAS - desde + 1
        if restantes <= 0:
            raise OnlineError("El alumno ya tiene pagadas todas sus semanas.")
        if n < 1 or n > restantes:
            raise OnlineError(f"El número de semanas debe ser entre 1 y {restantes}.")
        f = hoy()
        detalle = []
        for g in range(desde, desde + n):
            ini_g = inicio_semana(grupo, g)
            pos = plan["mapa"][g - 1]
            inmediata = ini_g <= f
            detalle.append({
                "semana": g, "trimestre": pos["trimestre"], "bloque": pos["bloque"], "semana_bloque": pos["semana_bloque"],
                "inicio": _iso(ini_g),
                "se_habilita": _iso(f) if inmediata else _iso(ini_g),
                "inmediata": inmediata,
                "fecha_limite": _iso(fecha_limite(fecha_pago, grupo, g, al)),
            })
        return detalle

    @staticmethod
    def _preparar(cur, id_alumno, bloquear=False):
        al = _alumno(cur, id_alumno, bloquear)
        if (al.get("modalidad_estudio") or "") != "ONLINE":
            raise OnlineError("El alumno no está en modalidad online.")
        ctx = _Contexto(cur)
        grupo, plan, problema = ctx.calendario(al)
        if problema:
            raise OnlineError(problema + ".")
        return al, grupo, plan, ctx

    @staticmethod
    def vista_previa_pago(id_alumno, semanas, fecha_pago=None):
        con = get_connection()
        cur = con.cursor()
        try:
            al, grupo, plan, _ = OnlineService._preparar(cur, id_alumno)
            pagadas = _contar_pagadas(cur, id_alumno)
            fp = _fecha(fecha_pago) or hoy()
            detalle = OnlineService._semanas_de_pago(al, grupo, plan, pagadas, int(semanas), fp)
            return {"success": True, "semanas": detalle, "estado": calcular_estado(al, grupo, plan, pagadas)}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def registrar_pago(id_alumno, data, usuario="SISTEMA"):
        con = get_connection()
        cur = con.cursor()
        try:
            al, grupo, plan, ctx = OnlineService._preparar(cur, id_alumno, bloquear=True)
            try:
                n = int(data.get("semanas") or data.get("semanas_pagadas") or 1)
                monto = float(data.get("monto") or 0)
            except (TypeError, ValueError):
                raise OnlineError("Semanas o monto inválidos.")
            if monto <= 0:
                raise OnlineError("El monto debe ser mayor a cero.")
            fp = _fecha(data.get("fecha_pago")) or hoy()
            if fp > hoy():
                raise OnlineError("La fecha del pago no puede ser futura.")
            metodo = str(data.get("metodo_pago") or "EFECTIVO").upper()
            if metodo not in METODOS_PAGO:
                raise OnlineError("Método de pago no válido.")
            folio = str(data.get("folio_ticket") or "").strip()[:60] or generar_folio()

            pagadas = _contar_pagadas(cur, id_alumno)
            detalle = OnlineService._semanas_de_pago(al, grupo, plan, pagadas, n, fp)
            desde, hasta = detalle[0]["semana"], detalle[-1]["semana"]

            cur.execute("""
                INSERT INTO tb_alumno_pagos
                    (id_alumno, fecha_pago, folio_ticket, semana_cubierta, semanas_pagadas, id_nivel_academico, mes_bloque,
                     semana_desde, semana_hasta, monto, metodo_pago, observaciones, registrado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (id_alumno, fp, folio, desde, n, detalle[0]["trimestre"], detalle[0]["bloque"], desde, hasta, monto, metodo,
                  (data.get("observaciones") or "").strip() or None, usuario))
            id_pago = cur.lastrowid
            for d in detalle:
                cur.execute("""
                    INSERT INTO tb_alumno_semanas_online (id_alumno, semana_global, id_pago, fecha_pago, estatus)
                    VALUES (%s, %s, %s, %s, 'EN_ESPERA')
                """, (id_alumno, d["semana"], id_pago, fp))
            con.commit()

            resultado = habilitar_alumno(con, cur, id_alumno, ctx)
            sin_error = 0 if resultado["errores_moodle"] else 1
            cur.execute("UPDATE tb_alumno_pagos SET sincronizado_moodle = %s, fecha_sincronizacion_moodle = IF(%s, NOW(), NULL) WHERE id = %s",
                        (sin_error, sin_error, id_pago))
            est = _actualizar_resumen_alumno(cur, al, grupo, plan)
            con.commit()
            return {
                "success": True,
                "pago": {"id": id_pago, "folio_ticket": folio, "semana_desde": desde, "semana_hasta": hasta,
                         "semanas": n, "monto": monto, "fecha_pago": _iso(fp)},
                "semanas": detalle,
                "habilitadas_hoy": resultado["habilitadas"],
                "errores_moodle": resultado["errores_moodle"],
                "estado": est,
            }, 201
        except Exception:
            con.rollback()
            raise
        finally:
            cur.close()
            con.close()

    # -------------------------------------------------------------- proceso de los sábados

    @staticmethod
    def habilitar_pendientes():
        """Habilita las semanas pagadas por adelantado cuya fecha llegó y reintenta las que fallaron en Moodle."""
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT s.id_alumno FROM tb_alumno_semanas_online s
                JOIN tb_alumnos a ON a.idAlumno = s.id_alumno AND a.modalidad_estudio = 'ONLINE'
                WHERE s.estatus = 'EN_ESPERA' OR s.moodle_sincronizado = 0
            """)
            ids = [r["id_alumno"] for r in cur.fetchall()]
            ctx = _Contexto(cur)
            resumen = {"alumnos": len(ids), "semanas_habilitadas": 0, "con_error": []}
            for id_alumno in ids:
                try:
                    r = habilitar_alumno(con, cur, id_alumno, ctx)
                    al = _alumno(cur, id_alumno)
                    grupo, plan, problema = ctx.calendario(al)
                    if not problema:
                        _actualizar_resumen_alumno(cur, al, grupo, plan)
                        con.commit()
                    resumen["semanas_habilitadas"] += len(r["habilitadas"])
                    if r["errores_moodle"]:
                        resumen["con_error"].append({"idAlumno": id_alumno, "errores": r["errores_moodle"]})
                except Exception as e:  # un alumno no detiene a los demás
                    con.rollback()
                    resumen["con_error"].append({"idAlumno": id_alumno, "errores": [str(e)]})
            return {"success": True, **resumen}, 200
        finally:
            cur.close()
            con.close()

    # -------------------------------------------------------------- Moodle manual

    @staticmethod
    def sincronizar_moodle(id_alumno):
        """Crea la cuenta si falta y vuelve a aplicar en Moodle todas las semanas habilitadas."""
        con = get_connection()
        cur = con.cursor()
        try:
            al, grupo, plan, ctx = OnlineService._preparar(cur, id_alumno)
            _, err = asegurar_usuario_moodle(cur, al)
            con.commit()
            if err:
                return {"success": False, "message": err}, 502
            cur.execute("UPDATE tb_alumno_semanas_online SET moodle_sincronizado = 0 WHERE id_alumno = %s AND estatus = 'HABILITADA'", (id_alumno,))
            con.commit()
            r = habilitar_alumno(con, cur, id_alumno, ctx)
            ok = not r["errores_moodle"]
            return {"success": ok, "moodle_username": al.get("moodle_username"), "habilitadas": r["habilitadas"],
                    "message": "Moodle sincronizado." if ok else " ".join(r["errores_moodle"])}, (200 if ok else 502)
        finally:
            cur.close()
            con.close()

    @staticmethod
    def suspension_manual(id_alumno, suspender):
        con = get_connection()
        cur = con.cursor()
        try:
            al = _alumno(cur, id_alumno)
            if not al.get("moodle_user_id"):
                return {"success": False, "message": "El alumno no tiene cuenta de Moodle."}, 400
            ok, err = MoodleService.suspender_usuario(int(al["moodle_user_id"]), suspender)
            if not ok:
                return {"success": False, "message": err}, 502
            return {"success": True, "message": "Cuenta de Moodle suspendida." if suspender else "Cuenta de Moodle reactivada."}, 200
        finally:
            cur.close()
            con.close()

    # -------------------------------------------------------------- cambio de modalidad

    @staticmethod
    def vista_integracion(id_alumno):
        """Qué pasaría si hoy se pasa al alumno a online: trimestre, fecha de inicio o motivo por el que no se puede."""
        con = get_connection()
        cur = con.cursor()
        try:
            al = _alumno(cur, id_alumno)
            grupo = _Contexto(cur).grupo(al.get("idGrupo"))
            v = ventana_cambio(grupo)
            pagadas = _contar_pagadas(cur, id_alumno)
            if v["permitido"] and pagadas:
                v = {"permitido": False, "mensaje": "El alumno ya tiene semanas online pagadas; no se puede reiniciar su calendario."}
            return {
                "success": True,
                "alumno": {"idAlumno": al["idAlumno"], "nombreCompleto": _nombre(al), "numeroControl": al["numeroControl"],
                           "modalidad_estudio": al["modalidad_estudio"], "moodle_username": al.get("moodle_username") or username_moodle(al)},
                "grupo": grupo and {"id": grupo["id"], "clave": grupo["clave"], "dia_clase": grupo["dia_clase"]},
                "ventana": v,
            }, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def cambiar_modalidad_online(id_alumno, data):
        con = get_connection()
        cur = con.cursor()
        try:
            al = _alumno(cur, id_alumno, bloquear=True)
            ctx = _Contexto(cur)
            grupo = ctx.grupo(al.get("idGrupo"))
            v = ventana_cambio(grupo)
            if not v["permitido"]:
                raise OnlineError(v["mensaje"])
            plan = ctx.plan(grupo["id_plan"])
            if not plan["mapa"]:
                raise OnlineError("El plan de bloques está incompleto: " + " ".join(plan["errores"]))
            if _contar_pagadas(cur, id_alumno):
                raise OnlineError("El alumno ya tiene semanas online pagadas; no se puede reiniciar su calendario.")
            dia = str(data.get("dia_pago") or grupo["dia_clase"]).upper()
            if dia not in DIAS_COBRO:
                raise OnlineError("El día de cobro debe ser sábado o domingo.")

            # Validar y crear la cuenta en Moodle PRIMERO: si falla, no se toca el alumno
            moodle_user_id, err_moodle = asegurar_usuario_moodle(cur, al, data.get("moodle_password"))
            if err_moodle:
                con.rollback()
                raise OnlineError(f"No se pudo crear la cuenta en Moodle: {err_moodle}. El alumno no fue integrado a la modalidad online.")

            al["dia_pago"] = dia
            al["semana_inicio_online"] = v["semana_inicio"]
            cur.execute("""
                UPDATE tb_alumnos SET modalidad_estudio = 'ONLINE', dia_pago = %s,
                    semana_inicio_online = %s, trimestre_inicio_online = %s
                WHERE idAlumno = %s
            """, (dia, v["semana_inicio"], v["trimestre"], id_alumno))

            est = _actualizar_resumen_alumno(cur, al, grupo, plan)
            con.commit()
            cur.execute("SELECT moodle_username, moodle_password FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))
            cred = cur.fetchone()
            return {
                "success": True,
                "message": "Alumno integrado a modalidad online exitosamente.",
                "grupo": grupo["clave"],
                "trimestre": v["trimestre"],
                "inicio_trimestre": v["inicio"],
                "moodle": {"ok": True, "error": None, "username": cred["moodle_username"], "password": cred["moodle_password"]},
                "estado": est,
            }, 200
        except Exception:
            con.rollback()
            raise
        finally:
            cur.close()
            con.close()

    @staticmethod
    def cambiar_modalidad_presencial(id_alumno):
        """Regresa a presencial (mismo grupo) y suspende la cuenta de Moodle (decisión del administrativo, no por adeudo)."""
        con = get_connection()
        cur = con.cursor()
        try:
            al = _alumno(cur, id_alumno)
            cur.execute("UPDATE tb_alumnos SET modalidad_estudio = 'PRESENCIAL' WHERE idAlumno = %s", (id_alumno,))
            con.commit()
            aviso = None
            if al.get("moodle_user_id"):
                ok, err = MoodleService.suspender_usuario(int(al["moodle_user_id"]), True)
                aviso = None if ok else err
            return {"success": True, "mensaje": "Alumno retornado a modalidad presencial.", "aviso_moodle": aviso}, 200
        finally:
            cur.close()
            con.close()

    # -------------------------------------------------------------- configuración

    @staticmethod
    def listar_grupos():
        """Grupos BGNE activos con su calendario (para configuración y consulta)."""
        con = get_connection()
        cur = con.cursor()
        try:
            ctx = _Contexto(cur)
            cur.execute("""
                SELECT g.id,
                       SUM(a.modalidad_estudio = 'ONLINE') AS online, SUM(COALESCE(a.modalidad_estudio, 'PRESENCIAL') <> 'ONLINE') AS presencial
                FROM tb_grupos g LEFT JOIN tb_alumnos a ON a.idGrupo = g.id
                WHERE g.id_centroTrabajo = %s AND g.statusGrupo = 'ACTIVO'
                GROUP BY g.id
            """, (CCT_BGNE,))
            conteos = {r["id"]: r for r in cur.fetchall()}
            f = hoy()
            salida = []
            for id_grupo, c in conteos.items():
                g = ctx.grupo(id_grupo)
                fila = {"id": g["id"], "clave": g["clave"], "fecha_inicio": _iso(g["fecha_clase"]), "fecha_fin": _iso(_fecha(g["fechaFin"])),
                        "dia_clase": g["dia_clase"], "id_plan_online": g["id_plan_online"], "id_plan": g["id_plan"],
                        "alumnos_online": int(c["online"] or 0), "alumnos_presencial": int(c["presencial"] or 0)}
                if g["fecha_inicio"]:
                    sem = semana_calendario(g, f)
                    fila["semana_actual"] = sem
                    fila["trimestre_actual"] = (sem - 1) // SEMANAS_TRIMESTRE + 1 if 1 <= sem <= TOTAL_SEMANAS else None
                    fila["inicio_trimestres"] = {t: _iso(clase_inicio_trimestre(g, t)) for t in range(1, 7)}
                fila["ventana"] = ventana_cambio(g, f)
                salida.append(fila)
            salida.sort(key=lambda x: x.get("fecha_inicio") or "", reverse=True)
            return {"success": True, "grupos": salida}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def asignar_plan_grupo(id_grupo, id_plan):
        con = get_connection()
        cur = con.cursor()
        try:
            g = _Contexto(cur).grupo(id_grupo)
            if not g or not g["es_bgne"]:
                raise OnlineError("Grupo BGNE no encontrado.", 404)
            id_plan = int(id_plan) if str(id_plan or "").strip() else None
            if id_plan:
                cargar_plan(cur, id_plan)
            cur.execute("""
                SELECT COUNT(*) AS n FROM tb_alumno_semanas_online s JOIN tb_alumnos a ON a.idAlumno = s.id_alumno
                WHERE a.idGrupo = %s
            """, (id_grupo,))
            if cur.fetchone()["n"] and (id_plan or None) != (g["id_plan_online"] or None):
                raise OnlineError("El grupo ya tiene alumnos online con semanas pagadas; no se puede cambiar su plan de bloques.")
            cur.execute("UPDATE tb_grupos SET id_plan_online = %s WHERE id = %s", (id_plan, id_grupo))
            con.commit()
            return {"success": True, "message": "Plan del grupo actualizado."}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def listar_planes():
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("SELECT id FROM tb_online_planes ORDER BY id")
            planes = []
            for r in cur.fetchall():
                p = cargar_plan(cur, r["id"])
                p.pop("mapa", None)
                planes.append({k: _iso(v) for k, v in p.items() if k != "bloques"} | {"bloques": p["bloques"]})
            return {"success": True, "planes": planes}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def actualizar_bloques(id_plan, bloques):
        """bloques = [{id, semanas}]. Los 3 bloques de cada trimestre deben sumar 13."""
        con = get_connection()
        cur = con.cursor()
        try:
            actual = cargar_plan(cur, id_plan)["bloques"]
            cambios = {int(b["id"]): int(b["semanas"]) for b in (bloques or []) if b.get("id") is not None}
            for b in actual:
                if b["id"] in cambios:
                    if not 1 <= cambios[b["id"]] <= SEMANAS_TRIMESTRE:
                        raise OnlineError("Cada bloque debe durar entre 1 y 13 semanas.")
                    b["semanas"] = cambios[b["id"]]
            errores = validar_bloques(actual)
            if errores:
                raise OnlineError(" ".join(errores))
            for b in actual:
                if b["id"] in cambios:
                    cur.execute("UPDATE tb_online_plan_bloques SET semanas = %s WHERE id = %s AND id_plan = %s", (b["semanas"], b["id"], id_plan))
            con.commit()
            return {"success": True, "message": "Duración de bloques guardada."}, 200
        except Exception:
            con.rollback()
            raise
        finally:
            cur.close()
            con.close()

    @staticmethod
    def actualizar_curso(id_curso, data):
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("SELECT id FROM tb_online_bloque_cursos WHERE id = %s", (id_curso,))
            if not cur.fetchone():
                raise OnlineError("Curso no encontrado.", 404)
            campos, vals = [], []
            if "moodle_course_id" in data:
                v = data.get("moodle_course_id")
                try:
                    v = int(v) if str(v or "").strip() else None
                except ValueError:
                    raise OnlineError("El ID de curso de Moodle debe ser un número.")
                if v is not None and v <= 1:
                    raise OnlineError("El ID de curso de Moodle debe ser mayor a 1.")
                campos.append("moodle_course_id = %s")
                vals.append(v)
            if str(data.get("nombre") or "").strip():
                campos.append("nombre = %s")
                vals.append(str(data["nombre"]).strip()[:200])
            if not campos:
                raise OnlineError("No hay cambios.")
            cur.execute(f"UPDATE tb_online_bloque_cursos SET {', '.join(campos)} WHERE id = %s", [*vals, id_curso])
            con.commit()
            return {"success": True, "message": "Curso actualizado."}, 200
        finally:
            cur.close()
            con.close()

    @staticmethod
    def preparar_grupos_curso(id_curso):
        """Crea en Moodle los grupos Semana_1..Semana_N del curso (N = semanas de su bloque)."""
        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT c.nombre, c.moodle_course_id, b.semanas FROM tb_online_bloque_cursos c
                JOIN tb_online_plan_bloques b ON b.id = c.id_plan_bloque WHERE c.id = %s
            """, (id_curso,))
            c = cur.fetchone()
            if not c:
                raise OnlineError("Curso no encontrado.", 404)
            if not c["moodle_course_id"]:
                raise OnlineError("Primero captura el ID del curso de Moodle.")
            ok, grupos = MoodleService.asegurar_grupos_semana(int(c["moodle_course_id"]), int(c["semanas"]))
            if not ok:
                return {"success": False, "message": str(grupos)}, 502
            nombres = [f"Semana_{s}" for s in range(1, int(c["semanas"]) + 1)]
            return {"success": True, "message": f"Grupos listos en el curso {c['moodle_course_id']}: {', '.join(nombres)}."}, 200
        finally:
            cur.close()
            con.close()
