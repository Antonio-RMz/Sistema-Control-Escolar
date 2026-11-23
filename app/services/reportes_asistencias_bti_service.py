"""
Reportes estadísticos de asistencias para grupos BTI (id_centroTrabajo = 2).

Cómo se pasa lista en BTI:
  - Lo hace Administración, UNA vez al día (en la mañana), con el "Pase General".
    El pase general guarda una fila por materia del horario, pero todas con el mismo
    estatus: la unidad real de medida es el DÍA (alumno, fecha).
  - Si un día tiene filas con estatus distintos, gana la editada más recientemente
    (ej. una falta que después se cambió a justificante).

Reglas de negocio (definidas por la escuela):
  - A  = asistió.
  - R  = llegó tarde: cuenta como ASISTENCIA, pero se conserva y reporta el retardo.
  - F  = no vino.
  - J  = no vino, pero avisó / pidió permiso / entregó justificante. NO es asistencia
         (físicamente no llegó): es una FALTA JUSTIFICADA. Puede registrarse el mismo día
         o editarse después sobre una falta. También cuentan los justificantes de
         Administración (tb_justificaciones_alumnos).
  - Resumen de boleta: asistencias del total de días con pase de lista, faltas totales
    y, de esas faltas, cuántas y cuándo se justificaron.
  - No hay umbral de riesgo por ahora.
  - Días especiales del grupo: INHABIL y SUSPENSION no cuentan como día de clase ni como falta
    (su pase, si lo hubo, se ignora). EN_LINEA sí es día de clase y cuenta como asistencia
    aunque no se haya pasado lista; si hubo pase, se respeta la marca capturada.
"""
import datetime
from app.config.conexion import get_connection
from app.services.asistencias_alumnos_service import AsistenciasAlumnosService

CCT_BTI = 2

DIAS_NOMBRE = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
ESTATUS_VALIDOS = ('A', 'R', 'F', 'J')


def _to_date(val):
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    return datetime.datetime.strptime(str(val)[:10], '%Y-%m-%d').date()


def _iso(val):
    if val is None:
        return None
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat(sep=' ') if isinstance(val, datetime.datetime) else val.isoformat()
    return str(val)


def _pct(parte, total):
    return round(parte / total * 100, 1) if total > 0 else None


def _contadores():
    return {'A': 0, 'R': 0, 'F': 0, 'J': 0, 'SIN_REGISTRO': 0}


def _resumen(c):
    """Resumen estilo boleta a partir de los contadores por día."""
    dias_registrados = c['A'] + c['R'] + c['F'] + c['J']
    asistencias = c['A'] + c['R']
    faltas = c['F'] + c['J']
    return {
        'dias_registrados': dias_registrados,     # "del total que hubo"
        'asistencias': asistencias,               # A + R
        'retardos': c['R'],                       # incluidos en asistencias
        'faltas': faltas,                         # F + J
        'faltas_justificadas': c['J'],
        'faltas_sin_justificar': c['F'],
        'sin_registro': c['SIN_REGISTRO'],        # días con pase en el grupo, sin marca para el alumno
        'porcentaje_asistencia': _pct(asistencias, dias_registrados),
    }


class ReportesAsistenciasBtiService:

    # ------------------------------------------------------------------
    # Contexto común: grupo, rango, días de clase y estatus diario
    # ------------------------------------------------------------------
    @staticmethod
    def _cargar_contexto(cursor, id_grupo, desde=None, hasta=None, id_alumno=None, parcial=None):
        cursor.execute("""
            SELECT g.id, g.clave, g.fechaInicio, g.fechaFin, g.id_centroTrabajo, g.id_nivel_academico,
                   g.modalidadHorario, ct.nombre AS nombreCentroTrabajo
            FROM tb_grupos g
            LEFT JOIN tb_centrotrabajo ct ON ct.id = g.id_centroTrabajo
            WHERE g.id = %s
        """, (id_grupo,))
        grupo = cursor.fetchone()
        if not grupo:
            return None, ({'error': 'Grupo no encontrado'}, 404)
        if grupo.get('id_centroTrabajo') != CCT_BTI:
            return None, ({'error': 'Este reporte aplica solo a grupos BTI.'}, 400)

        inicio_grupo = _to_date(grupo['fechaInicio'])
        fin_grupo = _to_date(grupo['fechaFin'])
        if not inicio_grupo or not fin_grupo:
            return None, ({'error': 'El grupo no tiene fechas de inicio y fin configuradas.'}, 400)

        try:
            desde_d = _to_date(desde) if desde else None
            hasta_d = _to_date(hasta) if hasta else None
        except ValueError:
            return None, ({'error': 'Formato de fecha inválido (use AAAA-MM-DD).'}, 400)

        # Parcial: sus fechas se configuran en Horarios > "Fechas de Periodos de Evaluación"
        info_parcial = None
        if parcial:
            try:
                parcial = int(parcial)
            except (TypeError, ValueError):
                parcial = 0
            if parcial not in (1, 2, 3):
                return None, ({'error': 'El parcial debe ser 1, 2 o 3.'}, 400)
            cursor.execute(f"""
                SELECT p{parcial}_fecha_inicio AS inicio, p{parcial}_fecha_fin AS fin
                FROM tb_grupo_periodos_captura WHERE id_grupo = %s
            """, (id_grupo,))
            fechas_p = cursor.fetchone() or {}
            if not fechas_p.get('inicio') or not fechas_p.get('fin'):
                return None, ({'error': f'El grupo no tiene configuradas las fechas del {parcial}° parcial (Horarios > Fechas de Periodos de Evaluación).'}, 400)
            desde_d, hasta_d = _to_date(fechas_p['inicio']), _to_date(fechas_p['fin'])
            info_parcial = {'numero': parcial, 'inicio': desde_d.isoformat(), 'fin': hasta_d.isoformat()}

        # Rango efectivo: dentro del semestre y nunca después de hoy
        rango_inicio = max(inicio_grupo, desde_d) if desde_d else inicio_grupo
        rango_fin = min(fin_grupo, datetime.date.today())
        if hasta_d:
            rango_fin = min(rango_fin, hasta_d)
        rango_valido = rango_inicio <= rango_fin

        cursor.execute("SELECT id_nivel_academico FROM tb_grupo_periodos_captura WHERE id_grupo = %s", (id_grupo,))
        cfg = cursor.fetchone()
        nivel_activo = (cfg or {}).get('id_nivel_academico') or grupo.get('id_nivel_academico')
        nivel_info = None
        if nivel_activo:
            cursor.execute("SELECT id, nombre FROM tb_niveles_academicos WHERE id = %s", (nivel_activo,))
            nivel_info = cursor.fetchone()

        # Días de clase del grupo (mismo calendario que el pase de lista). BTI: lunes a viernes.
        cursor.execute("SELECT dia FROM tb_grupodias WHERE idGrupo = %s", (id_grupo,))
        dias_clase = [d['dia'] for d in (cursor.fetchall() or [])] or ['LUNES-VIERNES']
        dias_programados = (
            AsistenciasAlumnosService._generar_fechas_clase(rango_inicio, rango_fin, dias_clase)
            if rango_valido else []
        )

        if id_alumno:
            # Reporte/boleta de UN alumno: basta con que pertenezca al grupo, aunque hoy esté
            # inactivo (p. ej. reimprimir la boleta de un parcial de un alumno que ya se dio de baja)
            cursor.execute("""
                SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s AND a.idAlumno = %s
                LIMIT 1
            """, (id_grupo, id_alumno))
        else:
            # Reporte del grupo: alumnos activos (mismo criterio que el pase de lista)
            cursor.execute("""
                SELECT a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.numeroControl
                FROM tb_alumnogrupo ag
                JOIN tb_alumnos a ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s AND ag.estado = 'ACTIVO' AND a.statusAlumno = 'ACTIVO'
                ORDER BY a.apPaterno, a.apMaterno, a.nombre
            """, (id_grupo,))
        alumnos = cursor.fetchall() or []

        # Días especiales: inhábil y suspensión no son día de clase ni falta (se quitan del
        # calendario y su pase, si lo hubo, no se cuenta); en línea es día de clase normal.
        dias_especiales = (
            AsistenciasAlumnosService.get_dias_especiales(cursor, id_grupo, rango_inicio, rango_fin)
            if rango_valido else {}
        )
        sin_clase = {f for f, d in dias_especiales.items() if d['tipo'] in AsistenciasAlumnosService.TIPOS_SIN_CLASE}
        dias_programados = [f for f in dias_programados if f not in sin_clase]

        # Estatus diario: una fila por (alumno, fecha); gana la editada más recientemente
        registros = {}       # (id_alumno, fecha) -> {estatus, observaciones, actualizado}
        dias_con_pase = set()
        if rango_valido:
            cursor.execute("""
                SELECT id_alumno, fecha, estatus, observaciones, created_at, updated_at
                FROM tb_asistencias_alumnos
                WHERE id_grupo = %s AND fecha BETWEEN %s AND %s
                ORDER BY updated_at ASC, id ASC
            """, (id_grupo, rango_inicio, rango_fin))
            for r in cursor.fetchall() or []:
                if r['estatus'] not in ESTATUS_VALIDOS:
                    continue
                f = _to_date(r['fecha'])
                if f in sin_clase:
                    continue
                dias_con_pase.add(f)
                registros[(r['id_alumno'], f)] = {
                    'estatus': r['estatus'],
                    'observaciones': r.get('observaciones') or '',
                    'registrado': r.get('created_at'),
                    'actualizado': r.get('updated_at') or r.get('created_at'),
                }

        # Justificantes capturados por Administración (módulo "Justificar Faltas")
        justificantes_admin = {}  # (id_alumno, fecha) -> {motivo, registrado}
        if alumnos and rango_valido:
            ids = [a['idAlumno'] for a in alumnos]
            marcadores = ','.join(['%s'] * len(ids))
            cursor.execute(f"""
                SELECT id_alumno, fecha, motivo, created_at
                FROM tb_justificaciones_alumnos
                WHERE id_alumno IN ({marcadores}) AND fecha BETWEEN %s AND %s
            """, tuple(ids) + (rango_inicio, rango_fin))
            for j in cursor.fetchall() or []:
                if _to_date(j['fecha']) in sin_clase:
                    continue
                justificantes_admin[(j['id_alumno'], _to_date(j['fecha']))] = {
                    'motivo': j.get('motivo') or 'Justificado por Administración',
                    'registrado': j.get('created_at'),
                }

        # Clases en línea: son día de clase y cuentan como asistencia aunque no se haya pasado
        # lista (si hubo pase, se respeta la marca capturada: R, F o J). Se tratan como días
        # cubiertos para que entren al calendario, a la cobertura y al resumen por día.
        en_linea = {f for f, d in dias_especiales.items() if d['tipo'] == 'EN_LINEA'}
        dias_con_pase |= en_linea

        # Calendario evaluado: días programados + cualquier día con pase fuera de calendario
        calendario = sorted(set(dias_programados) | dias_con_pase)

        return {
            'grupo': grupo,
            'nivel': nivel_info,
            'parcial': info_parcial,
            'rango_inicio': rango_inicio,
            'rango_fin': rango_fin,
            'rango_valido': rango_valido,
            'inicio_grupo': inicio_grupo,
            'fin_grupo': fin_grupo,
            'dias_programados': set(dias_programados),
            'dias_con_pase': dias_con_pase,
            'calendario': calendario,
            'alumnos': alumnos,
            'registros': registros,
            'justificantes_admin': justificantes_admin,
            'dias_especiales': dias_especiales,
            'en_linea': en_linea,
        }, None

    @staticmethod
    def _estado_dia(ctx, id_alumno, fecha):
        """
        Estatus efectivo del alumno en un día:
          A/R/F/J        -> registrado en el pase de lista (o justificante de Administración)
          SIN_REGISTRO   -> el grupo tuvo pase ese día, pero el alumno quedó sin marca
          SIN_PASE       -> ese día no se pasó lista al grupo
        Devuelve dict con estatus, observaciones, origen del justificante y fechas de registro.
        """
        just = ctx['justificantes_admin'].get((id_alumno, fecha))
        if just is not None:
            return {'estatus': 'J', 'observaciones': just['motivo'], 'origen': 'ADMINISTRACION',
                    'registrado': just['registrado'], 'actualizado': just['registrado']}
        reg = ctx['registros'].get((id_alumno, fecha))
        if reg:
            return {'estatus': reg['estatus'], 'observaciones': reg['observaciones'],
                    'origen': 'PASE_DE_LISTA' if reg['estatus'] == 'J' else None,
                    'registrado': reg['registrado'], 'actualizado': reg['actualizado']}
        if fecha in ctx['en_linea']:
            # Clase en línea sin marca del alumno: cuenta como asistencia
            return {'estatus': 'A', 'observaciones': 'Clase en línea', 'origen': 'EN_LINEA',
                    'registrado': None, 'actualizado': None}
        if fecha in ctx['dias_con_pase']:
            return {'estatus': 'SIN_REGISTRO', 'observaciones': '', 'origen': None, 'registrado': None, 'actualizado': None}
        return {'estatus': 'SIN_PASE', 'observaciones': '', 'origen': None, 'registrado': None, 'actualizado': None}

    @staticmethod
    def _info_grupo(ctx):
        g = ctx['grupo']
        return {
            'id': g['id'],
            'clave': g.get('clave') or '',
            'centroTrabajo': g.get('nombreCentroTrabajo') or 'BTI',
            'modalidad': g.get('modalidadHorario') or '',
            'nivel': (ctx['nivel'] or {}).get('nombre'),
            'id_nivel': (ctx['nivel'] or {}).get('id'),
            'fechaInicio': ctx['inicio_grupo'].isoformat(),
            'fechaFin': ctx['fin_grupo'].isoformat(),
        }

    @staticmethod
    def _info_rango(ctx):
        return {
            'desde': ctx['rango_inicio'].isoformat(),
            'hasta': ctx['rango_fin'].isoformat(),
            'vacio': not ctx['rango_valido'],
            'parcial': ctx.get('parcial'),   # {numero, inicio, fin} si se pidió un parcial
        }

    @staticmethod
    def _info_cobertura(ctx):
        programados = len(ctx['dias_programados'])
        con_pase = len(ctx['dias_con_pase'] & ctx['dias_programados'])
        sin_pase = sorted(ctx['dias_programados'] - ctx['dias_con_pase'])
        return {
            'dias_programados': programados,
            'dias_con_pase': con_pase,
            'dias_sin_pase': len(sin_pase),
            'fechas_sin_pase': [f.isoformat() for f in sin_pase],
            'dias_con_pase_fuera_calendario': len(ctx['dias_con_pase'] - ctx['dias_programados']),
            'porcentaje': _pct(con_pase, programados),
        }

    @staticmethod
    def _nombre(al):
        return f"{al.get('apPaterno') or ''} {al.get('apMaterno') or ''} {al.get('nombre') or ''}".strip()

    # ------------------------------------------------------------------
    # Reporte del grupo
    # ------------------------------------------------------------------
    @staticmethod
    def get_reporte_grupo(id_grupo, desde=None, hasta=None, parcial=None):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ctx, err = ReportesAsistenciasBtiService._cargar_contexto(cursor, id_grupo, desde, hasta, parcial=parcial)
            if err:
                return err

            cont_grupo = _contadores()
            asistencia_por_dia = {f: _contadores() for f in sorted(ctx['dias_con_pase'])}
            alumnos_out = []

            for al in ctx['alumnos']:
                aid = al['idAlumno']
                c = _contadores()
                for fecha in ctx['calendario']:
                    est = ReportesAsistenciasBtiService._estado_dia(ctx, aid, fecha)['estatus']
                    if est == 'SIN_PASE':
                        continue
                    c[est] += 1
                    cont_grupo[est] += 1
                    if fecha in asistencia_por_dia:
                        asistencia_por_dia[fecha][est] += 1
                alumnos_out.append({
                    'idAlumno': aid,
                    'nombreCompleto': ReportesAsistenciasBtiService._nombre(al),
                    'numeroControl': al.get('numeroControl') or '',
                    **_resumen(c),
                })

            resumen = _resumen(cont_grupo)
            resumen['total_alumnos'] = len(ctx['alumnos'])

            por_dia = []
            for fecha, c in asistencia_por_dia.items():
                r = _resumen(c)
                por_dia.append({
                    'fecha': fecha.isoformat(),
                    'dia_nombre': DIAS_NOMBRE.get(fecha.isoweekday(), ''),
                    'asistencias': r['asistencias'],
                    'retardos': r['retardos'],
                    'faltas': r['faltas'],
                    'faltas_justificadas': r['faltas_justificadas'],
                    'sin_registro': r['sin_registro'],
                    'porcentaje_asistencia': r['porcentaje_asistencia'],
                })

            return {
                'success': True,
                'tipo': 'BTI',
                'grupo': ReportesAsistenciasBtiService._info_grupo(ctx),
                'rango': ReportesAsistenciasBtiService._info_rango(ctx),
                'cobertura': ReportesAsistenciasBtiService._info_cobertura(ctx),
                'dias_especiales': AsistenciasAlumnosService.dias_especiales_lista(ctx['dias_especiales']),
                'resumen': resumen,
                'alumnos': alumnos_out,
                'por_dia': por_dia,
            }
        finally:
            cursor.close()
            conn.close()

    # ------------------------------------------------------------------
    # Reporte individual del alumno (resumen de boleta + justificantes + historial)
    # ------------------------------------------------------------------
    @staticmethod
    def get_reporte_alumno(id_grupo, id_alumno, desde=None, hasta=None, parcial=None):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            ctx, err = ReportesAsistenciasBtiService._cargar_contexto(cursor, id_grupo, desde, hasta, id_alumno=id_alumno, parcial=parcial)
            if err:
                return err
            if not ctx['alumnos']:
                return {'error': 'El alumno no pertenece a este grupo.'}, 404

            al = ctx['alumnos'][0]
            c = _contadores()
            historial = []
            faltas = []

            for fecha in ctx['calendario']:
                e = ReportesAsistenciasBtiService._estado_dia(ctx, id_alumno, fecha)
                if e['estatus'] != 'SIN_PASE':
                    c[e['estatus']] += 1
                dia = {
                    'fecha': fecha.isoformat(),
                    'dia_nombre': DIAS_NOMBRE.get(fecha.isoweekday(), ''),
                    'estatus': e['estatus'],
                    'observaciones': e['observaciones'],
                    'origen_justificante': e['origen'],
                    'actualizado': _iso(e['actualizado']),
                    'en_linea': (ctx['dias_especiales'].get(fecha) or {}).get('tipo') == 'EN_LINEA',
                }
                historial.append(dia)

                if e['estatus'] in ('F', 'J'):
                    faltas.append({
                        'fecha': fecha.isoformat(),
                        'dia_nombre': dia['dia_nombre'],
                        'justificada': e['estatus'] == 'J',
                        'origen': e['origen'],
                        'motivo': e['observaciones'],
                        # Cuándo se capturó el justificante (si se editó después, es la fecha de edición)
                        'fecha_justificacion': _iso(e['actualizado']) if e['estatus'] == 'J' else None,
                    })

            historial.reverse()
            faltas.reverse()

            return {
                'success': True,
                'tipo': 'BTI',
                'grupo': ReportesAsistenciasBtiService._info_grupo(ctx),
                'rango': ReportesAsistenciasBtiService._info_rango(ctx),
                'cobertura': ReportesAsistenciasBtiService._info_cobertura(ctx),
                'alumno': {
                    'idAlumno': al['idAlumno'],
                    'nombreCompleto': ReportesAsistenciasBtiService._nombre(al),
                    'numeroControl': al.get('numeroControl') or '',
                },
                'dias_especiales': AsistenciasAlumnosService.dias_especiales_lista(ctx['dias_especiales']),
                'resumen': _resumen(c),
                'faltas': faltas,
                'historial': historial,
            }
        finally:
            cursor.close()
            conn.close()
