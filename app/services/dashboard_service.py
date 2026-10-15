from decimal import Decimal
from datetime import date, datetime
from app.config.conexion import get_connection

class DashboardService:

    @staticmethod
    def get_stats():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Alumnos y modalidades
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_alumnos,
                    SUM(CASE WHEN statusAlumno = 'ACTIVO' THEN 1 ELSE 0 END) as alumnos_activos,
                    SUM(CASE WHEN statusAlumno = 'CERTIFICADO' THEN 1 ELSE 0 END) as alumnos_certificados,
                    SUM(CASE WHEN statusAlumno = 'INACTIVO' THEN 1 ELSE 0 END) as alumnos_inactivos,
                    SUM(CASE WHEN modalidad_estudio = 'ONLINE' THEN 1 ELSE 0 END) as modalidad_online,
                    SUM(CASE WHEN modalidad_estudio = 'PRESENCIAL' OR modalidad_estudio IS NULL THEN 1 ELSE 0 END) as modalidad_presencial
                FROM tb_alumnos
            """)
            alumnos_row = cursor.fetchone() or {}

            # 2. Docentes
            cursor.execute("SELECT COUNT(*) as total FROM tb_docentes WHERE statusDocente = 1 OR statusDocente = 'ACTIVO' OR 1=1")
            docentes_cnt = (cursor.fetchone() or {}).get('total', 0)

            # 3. Grupos
            cursor.execute("SELECT COUNT(*) as total FROM tb_grupos WHERE statusGrupo = 'ACTIVO' OR 1=1")
            grupos_cnt = (cursor.fetchone() or {}).get('total', 0)

            # 4. Materias
            cursor.execute("SELECT COUNT(*) as total FROM tb_materias WHERE estatusMateria = 1 OR estatusMateria = 'ACTIVO' OR 1=1")
            materias_cnt = (cursor.fetchone() or {}).get('total', 0)

            # 5. Asistencias
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN estatus = 'A' THEN 1 ELSE 0 END) as presentes,
                    SUM(CASE WHEN estatus = 'F' THEN 1 ELSE 0 END) as faltas,
                    SUM(CASE WHEN estatus = 'R' THEN 1 ELSE 0 END) as retardos,
                    SUM(CASE WHEN estatus = 'J' THEN 1 ELSE 0 END) as justificaciones
                FROM tb_asistencias_alumnos
            """)
            asist_row = cursor.fetchone() or {}
            tot_asist = int(asist_row.get('total') or 0)
            presentes = int(asist_row.get('presentes') or 0)
            faltas = int(asist_row.get('faltas') or 0)
            retardos = int(asist_row.get('retardos') or 0)
            justificadas = int(asist_row.get('justificaciones') or 0)
            tasa_asistencia = round((presentes / tot_asist * 100), 1) if tot_asist > 0 else 100.0

            # 6. Calificaciones
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(calificacion) as promedio,
                    SUM(CASE WHEN calificacion >= 6 THEN 1 ELSE 0 END) as aprobados,
                    SUM(CASE WHEN calificacion < 6 THEN 1 ELSE 0 END) as reprobados
                FROM tb_calificaciones
            """)
            calif_row = cursor.fetchone() or {}
            tot_calif = int(calif_row.get('total') or 0)
            promedio = float(calif_row.get('promedio') or 0)
            aprobados = int(calif_row.get('aprobados') or 0)
            reprobados = int(calif_row.get('reprobados') or 0)
            tasa_aprobacion = round((aprobados / tot_calif * 100), 1) if tot_calif > 0 else 100.0

            # 7. Alumnos por Grupo
            cursor.execute("""
                SELECT 
                    g.id,
                    g.clave,
                    g.modalidad,
                    g.horario,
                    COUNT(ag.idAlumno) as total_alumnos
                FROM tb_grupos g
                LEFT JOIN tb_alumnogrupo ag ON ag.idGrupo = g.id
                GROUP BY g.id, g.clave, g.modalidad, g.horario
                ORDER BY total_alumnos DESC, g.clave ASC
            """)
            grupos_alumnos = cursor.fetchall() or []

            # 8. Reportes Recientes
            try:
                cursor.execute("""
                    SELECT id, folio, id_alumno, alumno_nombre, tutor_nombre, fecha, incidente, parcial
                    FROM tb_reportes_indisciplina
                    ORDER BY id DESC
                    LIMIT 5
                """)
                reportes = cursor.fetchall() or []
                for r in reportes:
                    if isinstance(r.get('fecha'), (date, datetime)):
                        r['fecha'] = r['fecha'].strftime('%d/%m/%Y')
            except Exception:
                reportes = []

            # 9. Centros de Trabajo / Programas
            cursor.execute("SELECT id, clave, nombre FROM tb_centrotrabajo")
            centros = cursor.fetchall() or []

            return {
                "success": True,
                "kpis": {
                    "total_alumnos": int(alumnos_row.get('total_alumnos') or 0),
                    "alumnos_activos": int(alumnos_row.get('alumnos_activos') or 0),
                    "alumnos_certificados": int(alumnos_row.get('alumnos_certificados') or 0),
                    "alumnos_inactivos": int(alumnos_row.get('alumnos_inactivos') or 0),
                    "modalidad_online": int(alumnos_row.get('modalidad_online') or 0),
                    "modalidad_presencial": int(alumnos_row.get('modalidad_presencial') or 0),
                    "total_docentes": int(docentes_cnt),
                    "total_grupos": int(grupos_cnt),
                    "total_materias": int(materias_cnt),
                    "tasa_asistencia": tasa_asistencia,
                    "presentes": presentes,
                    "faltas": faltas,
                    "retardos": retardos,
                    "justificaciones": justificadas,
                    "promedio_general": round(promedio, 2),
                    "aprobados": aprobados,
                    "reprobados": reprobados,
                    "tasa_aprobacion": tasa_aprobacion,
                    "total_reportes": len(reportes)
                },
                "charts": {
                    "grupos": [
                        {
                            "id": g['id'],
                            "clave": g['clave'],
                            "total": int(g['total_alumnos'])
                        }
                        for g in grupos_alumnos
                    ],
                    "estatus_alumnos": {
                        "activos": int(alumnos_row.get('alumnos_activos') or 0),
                        "certificados": int(alumnos_row.get('alumnos_certificados') or 0),
                        "inactivos": int(alumnos_row.get('alumnos_inactivos') or 0)
                    },
                    "asistencias": {
                        "presentes": presentes,
                        "faltas": faltas,
                        "retardos": retardos,
                        "justificaciones": justificadas
                    },
                    "calificaciones": {
                        "aprobados": aprobados,
                        "reprobados": reprobados
                    }
                },
                "centros": centros,
                "reportes_recientes": reportes
            }
        finally:
            cursor.close()
            conn.close()
