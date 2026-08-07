from app.config.conexion import get_connection
import pymysql
import datetime
from datetime import timedelta


class DocentesService:
    @staticmethod
    def get_docentes(page, limit, search, status):
        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            offset = (page - 1) * limit

            sql = """
                SELECT 
                    idDocente, 
                    nombreDocente, 
                    apPaternoDocente, 
                    apMaternoDocente, 
                    correoDocente, 
                    telefonoDocente, 
                    statusDocente, 
                    observacionesDocente,
                    nivelEstudios,
                    fechaNacimiento,
                    idBiometrico
                FROM tb_docentes
                WHERE 1=1
            """

            params = []

            #  Búsqueda
            if search:
                sql += """
                    AND (
                        nombreDocente LIKE %s OR 
                        apPaternoDocente LIKE %s OR 
                        apMaternoDocente LIKE %s
                    )
                """
                like = f"%{search}%"
                params.extend([like, like, like])

            # Filtro por status
            if status:
                sql += " AND statusDocente = %s"
                params.append(status)

            #  Paginación
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(sql, params)
            data = cursor.fetchall()

            return {"data": data, "page": page, "limit": limit}

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_docente(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente,nivelEstudios, fechaNacimiento, idBiometrico)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update_docente(id_docente, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE tb_docentes 
                SET nombreDocente = %s, apPaternoDocente = %s, apMaternoDocente = %s, 
                    correoDocente = %s, telefonoDocente = %s, statusDocente = %s, 
                    observacionesDocente = %s, nivelEstudios = %s, fechaNacimiento = %s,
                    idBiometrico = %s
                WHERE idDocente = %s
            """
            cursor.execute(
                query,
                (
                    data.get("nombreDocente"),
                    data.get("apPaternoDocente"),
                    data.get("apMaternoDocente"),
                    data.get("correoDocente"),
                    data.get("telefonoDocente"),
                    data.get("statusDocente"),
                    data.get("observacionesDocente"),
                    data.get("nivelEstudios"),
                    data.get("fechaNacimiento"),
                    data.get("idBiometrico"),
                    id_docente,
                ),
            )
            conexion.commit()
            return {"mensaje": "Docente actualizado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete_docente(idDocente):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Desvincular materias asociadas al docente (poner a NULL) para no eliminarlas
            cursor.execute("UPDATE tb_materias SET idDocente = NULL WHERE idDocente = %s", (idDocente,))
            
            # 2. Eliminar relaciones en tablas secundarias para evitar errores de llave foránea
            cursor.execute("DELETE FROM tb_asistencias_docentes WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_cursoextracurricular WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_grupodocentes WHERE idDocente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_horarios WHERE id_docente = %s", (idDocente,))
            cursor.execute("DELETE FROM tb_materiadocente WHERE idDocente = %s", (idDocente,))
            
            # 3. Eliminar el docente
            cursor.execute("DELETE FROM tb_docentes WHERE idDocente = %s", (idDocente,))
            conexion.commit()
            return {"mensaje": "Docente eliminado correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_horas_docentes(fecha_inicio_str, fecha_fin_str):
        try:
            d_inicio = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            d_fin = datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Las fechas deben tener el formato YYYY-MM-DD")

        if d_inicio > d_fin:
            raise ValueError("La fecha de inicio debe ser menor o igual a la fecha de fin")

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # 1. Obtener todos los docentes activos
            cursor.execute("""
                SELECT 
                    idDocente, 
                    CONCAT(nombreDocente, ' ', COALESCE(apPaternoDocente, ''), ' ', COALESCE(apMaternoDocente, '')) AS docente
                FROM tb_docentes
                WHERE statusDocente = 'ACTIVO'
                ORDER BY nombreDocente, apPaternoDocente, apMaternoDocente
            """)
            docentes = cursor.fetchall()

            if not docentes:
                return []

            # 2. Obtener los horarios de grupos vigentes dentro del rango solicitado
            cursor.execute("""
                SELECT 
                    h.id_docente,
                    h.diaSemana,
                    h.horaInicio,
                    h.horaFin,
                    g.fechaInicio,
                    g.fechaFin
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                WHERE g.fechaInicio <= %s AND g.fechaFin >= %s
            """, (fecha_fin_str, fecha_inicio_str))
            horarios = cursor.fetchall()

            # Organizar horarios por docente
            horarios_por_docente = {}
            for h in horarios:
                id_doc = h['id_docente']
                if id_doc not in horarios_por_docente:
                    horarios_por_docente[id_doc] = []
                horarios_por_docente[id_doc].append(h)

            # Generar la lista de fechas en el rango
            dias_rango = []
            curr = d_inicio
            while curr <= d_fin:
                dias_rango.append(curr)
                curr += timedelta(days=1)

            resultado = []

            for doc in docentes:
                id_docente = doc['idDocente']
                docente_nombre = doc['docente'].strip()
                slots_docente = horarios_por_docente.get(id_docente, [])

                dias_reporte = []
                for d in dias_rango:
                    db_weekday = d.weekday() + 1
                    fecha_str = d.strftime("%Y-%m-%d")

                    # Filtrar horarios del docente activos en este día de la semana y vigentes en esta fecha
                    # Agrupamos por (horaInicio, horaFin) para evitar contar múltiples materias en la misma hora
                    slots_dia_map = {}
                    for h in slots_docente:
                        # Convertir fechas de mysql a date de python si vienen como datetime.date
                        h_fecha_inicio = h['fechaInicio']
                        h_fecha_fin = h['fechaFin']
                        if isinstance(h_fecha_inicio, datetime.datetime):
                            h_fecha_inicio = h_fecha_inicio.date()
                        if isinstance(h_fecha_fin, datetime.datetime):
                            h_fecha_fin = h_fecha_fin.date()

                        if h['diaSemana'] == db_weekday and h_fecha_inicio <= d <= h_fecha_fin:
                            key = (h['horaInicio'], h['horaFin'])
                            slots_dia_map[key] = h

                    if not slots_dia_map:
                        dias_reporte.append({
                            "fecha": fecha_str,
                            "total": 0,
                            "real": 0
                        })
                        continue

                    # Calcular total de horas
                    total_minutos = 0
                    intervals = []
                    for start_td, end_td in slots_dia_map.keys():
                        
                        if isinstance(start_td, str):
                            h, m, s_val = map(int, start_td.split(':'))
                            start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(start_td, datetime.time):
                            start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                            
                        if isinstance(end_td, str):
                            h, m, s_val = map(int, end_td.split(':'))
                            end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                        elif isinstance(end_td, datetime.time):
                            end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)

                        diff_min = (end_td - start_td).total_seconds() / 60.0
                        total_minutos += diff_min
                        intervals.append((start_td.total_seconds() / 60.0, end_td.total_seconds() / 60.0))

                    total_horas = total_minutos / 60.0

                    # Calcular real de horas (unión de intervalos)
                    intervals.sort(key=lambda x: x[0])
                    merged = []
                    for start, end in intervals:
                        if not merged:
                            merged.append([start, end])
                        else:
                            prev_start, prev_end = merged[-1]
                            if start <= prev_end:
                                merged[-1][1] = max(prev_end, end)
                            else:
                                merged.append([start, end])
                    
                    real_minutos = sum(end - start for start, end in merged)
                    real_horas = real_minutos / 60.0

                    def format_hours(h):
                        h_round = round(h, 2)
                        return int(h_round) if h_round.is_integer() else h_round

                    dias_reporte.append({
                        "fecha": fecha_str,
                        "total": format_hours(total_horas),
                        "real": format_hours(real_horas)
                    })

                resultado.append({
                    "id_docente": id_docente,
                    "docente": docente_nombre,
                    "dias": dias_reporte
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_detalle_horas_docente(id_docente, fecha_str):
        try:
            d_fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD")

        # diaSemana: 1 (Lunes) a 7 (Domingo)
        db_weekday = d_fecha.weekday() + 1

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            # Consultar los horarios vigentes para el docente en este día de la semana y fecha
            # Un grupo está vigente si g.fechaInicio <= d_fecha <= g.fechaFin
            cursor.execute("""
                SELECT 
                    m.nombreMateria AS materia,
                    g.clave AS grupo,
                    h.aula,
                    h.horaInicio,
                    h.horaFin
                FROM tb_horarios h
                JOIN tb_grupos g ON h.id_grupo = g.id
                JOIN tb_materias m ON h.id_materia = m.id
                WHERE h.id_docente = %s 
                  AND h.diaSemana = %s
                  AND g.fechaInicio <= %s 
                  AND g.fechaFin >= %s
                ORDER BY h.horaInicio, m.nombreMateria
            """, (id_docente, db_weekday, fecha_str, fecha_str))
            
            rows = cursor.fetchall()
            
            resultado = []
            for r in rows:
                start_td = r['horaInicio']
                end_td = r['horaFin']
                
                # Convertir time/timedelta/string a timedelta para calcular duracion
                if isinstance(start_td, str):
                    h, m, s_val = map(int, start_td.split(':'))
                    start_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    start_str = r['horaInicio']
                elif isinstance(start_td, datetime.time):
                    start_str = start_td.strftime("%H:%M:%S")
                    start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                else: # timedelta
                    tot_sec = int(start_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    start_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                if isinstance(end_td, str):
                    h, m, s_val = map(int, end_td.split(':'))
                    end_td = timedelta(hours=h, minutes=m, seconds=s_val)
                    end_str = r['horaFin']
                elif isinstance(end_td, datetime.time):
                    end_str = end_td.strftime("%H:%M:%S")
                    end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)
                else: # timedelta
                    tot_sec = int(end_td.total_seconds())
                    hrs = tot_sec // 3600
                    mins = (tot_sec % 3600) // 60
                    secs = tot_sec % 60
                    end_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                diff_hours = (end_td - start_td).total_seconds() / 3600.0
                
                def format_hours(h):
                    h_round = round(h, 2)
                    return int(h_round) if h_round.is_integer() else h_round

                resultado.append({
                    "materia": r['materia'],
                    "grupo": r['grupo'],
                    "aula": r['aula'],
                    "hora_inicio": start_str,
                    "hora_fin": end_str,
                    "duracion": format_hours(diff_hours)
                })

            return resultado

        finally:
            cursor.close()
            conexion.close()
