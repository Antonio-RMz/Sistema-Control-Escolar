"""
Métricas del plantel (BTI o BGNE) para Administración.

Fase 1: resumen, asistencia y alumnos en riesgo.
  - La asistencia sale del PASE GENERAL (misma regla que la boleta BTI: justificantes de
    Administración, días inhábiles/suspensión fuera y clases en línea como asistencia).
    El pase de cada docente es un registro aparte y no entra aquí.
  - Periodo "actual": BTI = semestre del grupo; BGNE = trimestre en curso de cada grupo.
  - Riesgo: asistencia menor al umbral con un mínimo de días registrados.
"""
import datetime
from app.config.conexion import get_connection
from app.services.reportes_asistencias_bti_service import ReportesAsistenciasBtiService as RAB
from app.services.calificaciones_service import CalificacionesService

PLANTELES = {2: 'BTI', 3: 'BGNE'}
UMBRAL_ASISTENCIA = 80.0      # % mínimo de asistencia
MIN_DIAS_RIESGO = 3           # días registrados para evaluar riesgo
MIN_RETARDOS_TOP = 3          # retardos para entrar al top


def _pct(parte, total):
    return round(parte * 100 / total, 1) if total else None


class MetricasService:

    @staticmethod
    def _rango_grupo(grupo, es_bgne, periodo, desde, hasta, hoy):
        """(desde, hasta) del grupo según el periodo elegido; None si el grupo no aplica."""
        if periodo == 'personalizado':
            return desde, hasta
        if periodo in ('4s', '12s'):
            return hoy - datetime.timedelta(days=27 if periodo == '4s' else 83), hoy
        # actual
        if not es_bgne:
            return None, None   # el reporte usa las fechas del semestre del grupo
        trims = CalificacionesService.trimestres_grupo(grupo.get('fechaInicio'), grupo.get('fechaFin'))
        actual = next((t for t in trims if t['inicio'] <= hoy <= t['captura_fin']), None)
        if not actual:
            return 'omitir', 'El grupo no tiene un trimestre en curso.'
        return actual['inicio'], min(actual['fin'], hoy)

    @staticmethod
    def get_metricas(id_centro_trabajo, id_grupo=None, periodo='actual', desde=None, hasta=None):
        id_cct = int(id_centro_trabajo or 2)
        if id_cct not in PLANTELES:
            return {'success': False, 'error': 'Plantel no válido.'}, 400
        es_bgne = id_cct == 3
        hoy = datetime.date.today()
        if periodo == 'personalizado' and not (desde and hasta):
            return {'success': False, 'error': 'Indica las fechas desde y hasta.'}, 400

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, clave, fechaInicio, fechaFin FROM tb_grupos
                WHERE id_centroTrabajo = %s AND statusGrupo = 'ACTIVO'
                ORDER BY clave
            """, (id_cct,))
            grupos_plantel = cursor.fetchall() or []
            grupos = [g for g in grupos_plantel if not id_grupo or int(g['id']) == int(id_grupo)]

            tot = {'A': 0, 'R': 0, 'F': 0, 'J': 0, 'registros': 0, 'programados': 0, 'con_pase': 0, 'alumnos': 0}
            semanas = {}       # lunes -> contadores
            por_grupo, riesgo, retardos_top, omitidos = [], [], [], []
            rango_min, rango_max = None, None

            for g in grupos:
                d, h = MetricasService._rango_grupo(g, es_bgne, periodo, desde, hasta, hoy)
                if d == 'omitir':
                    omitidos.append({'clave': g['clave'], 'motivo': h})
                    continue
                ctx, err = RAB._cargar_contexto(cursor, g['id'], d, h, cualquier_plantel=True)
                if err:
                    omitidos.append({'clave': g['clave'], 'motivo': (err[0] or {}).get('error', 'Sin datos')})
                    continue
                if not ctx['rango_valido']:
                    omitidos.append({'clave': g['clave'], 'motivo': 'El periodo elegido queda fuera de las fechas del grupo.'})
                    continue
                calc = RAB.calcular_grupo(ctx)
                cob = RAB._info_cobertura(ctx)
                res = calc['resumen']
                nivel = (ctx['nivel'] or {}).get('nombre')
                rango_min = min(filter(None, [rango_min, ctx['rango_inicio']]))
                rango_max = max(filter(None, [rango_max, ctx['rango_fin']]))

                tot['A'] += res['asistencias'] - res['retardos']
                tot['R'] += res['retardos']
                tot['F'] += res['faltas_sin_justificar']
                tot['J'] += res['faltas_justificadas']
                tot['registros'] += res['dias_registrados']
                tot['programados'] += cob['dias_programados']
                tot['con_pase'] += cob['dias_con_pase']
                tot['alumnos'] += res['total_alumnos']

                por_grupo.append({
                    'id': g['id'], 'clave': g['clave'], 'nivel': nivel,
                    'alumnos': res['total_alumnos'],
                    'porcentaje_asistencia': res['porcentaje_asistencia'],
                    'asistencias': res['asistencias'], 'retardos': res['retardos'],
                    'faltas_sin_justificar': res['faltas_sin_justificar'],
                    'faltas_justificadas': res['faltas_justificadas'],
                    'cobertura_pase': cob['porcentaje'], 'dias_sin_pase': cob['dias_sin_pase'],
                    'desde': ctx['rango_inicio'].isoformat(), 'hasta': ctx['rango_fin'].isoformat(),
                })

                for dia in calc['por_dia']:
                    f = datetime.date.fromisoformat(dia['fecha'])
                    lunes = f - datetime.timedelta(days=f.weekday())
                    s = semanas.setdefault(lunes, {'asistencias': 0, 'retardos': 0, 'faltas': 0})
                    s['asistencias'] += dia['asistencias']
                    s['retardos'] += dia['retardos']
                    s['faltas'] += dia['faltas']

                for al in calc['alumnos']:
                    base = {'idAlumno': al['idAlumno'], 'nombre': al['nombreCompleto'],
                            'numeroControl': al['numeroControl'], 'id_grupo': g['id'], 'grupo': g['clave'],
                            'porcentaje_asistencia': al['porcentaje_asistencia'],
                            'faltas_sin_justificar': al['faltas_sin_justificar'],
                            'faltas_justificadas': al['faltas_justificadas'],
                            'retardos': al['retardos'], 'dias_registrados': al['dias_registrados']}
                    if (al['dias_registrados'] >= MIN_DIAS_RIESGO and al['porcentaje_asistencia'] is not None
                            and al['porcentaje_asistencia'] < UMBRAL_ASISTENCIA):
                        riesgo.append(base)
                    if al['retardos'] >= MIN_RETARDOS_TOP:
                        retardos_top.append(base)

            riesgo.sort(key=lambda a: (a['porcentaje_asistencia'], -a['faltas_sin_justificar']))
            retardos_top.sort(key=lambda a: -a['retardos'])
            tendencia = []
            for lunes in sorted(semanas):
                s = semanas[lunes]
                tendencia.append({'semana': lunes.isoformat(), **s,
                                  'porcentaje_asistencia': _pct(s['asistencias'], s['asistencias'] + s['faltas'])})

            asistencias = tot['A'] + tot['R']
            return {
                'success': True,
                'plantel': {'id': id_cct, 'nombre': PLANTELES[id_cct]},
                'periodo': {'tipo': periodo,
                            'desde': rango_min.isoformat() if rango_min else None,
                            'hasta': rango_max.isoformat() if rango_max else None},
                'umbrales': {'asistencia': UMBRAL_ASISTENCIA, 'min_dias': MIN_DIAS_RIESGO, 'retardos': MIN_RETARDOS_TOP},
                'kpis': {
                    'grupos': len(por_grupo),
                    'alumnos': tot['alumnos'],
                    'porcentaje_asistencia': _pct(asistencias, tot['registros']),
                    'asistencias': asistencias,
                    'retardos': tot['R'],
                    'faltas_sin_justificar': tot['F'],
                    'faltas_justificadas': tot['J'],
                    'cobertura_pase': _pct(tot['con_pase'], tot['programados']),
                    'alumnos_en_riesgo': len(riesgo),
                },
                'tendencia': tendencia,
                'grupos': sorted(por_grupo, key=lambda x: (x['porcentaje_asistencia'] is None, x['porcentaje_asistencia'] or 0)),
                'riesgo': riesgo,
                'retardos_top': retardos_top[:20],
                'grupos_lista': [{'id': g['id'], 'clave': g['clave']} for g in grupos_plantel],
                'omitidos': omitidos,
            }
        finally:
            cursor.close()
            conn.close()
