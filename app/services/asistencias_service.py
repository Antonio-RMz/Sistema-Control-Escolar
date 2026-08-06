import os
import re
import datetime
from datetime import timedelta
import pandas as pd
import pymysql
from app.config.conexion import get_connection

def str_from_td(td):
    if td is None:
        return "00:00:00"
    tot_sec = int(td.total_seconds())
    hrs = tot_sec // 3600
    mins = (tot_sec % 3600) // 60
    secs = tot_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

class AsistenciasService:
    @staticmethod
    def procesar_excel(file_stream):
        # 1. Leer el archivo Excel en memoria usando pandas
        xls = pd.ExcelFile(file_stream)
        sheet_name = None
        for name in xls.sheet_names:
            if "asistencia" in name.lower() or "reporte" in name.lower():
                sheet_name = name
                break
        if not sheet_name:
            sheet_name = xls.sheet_names[0]
            
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # 2. Buscar el Periodo de fechas
        period_str = None
        for r in range(min(10, len(df))):
            for c in range(len(df.columns)):
                val = str(df.iloc[r, c])
                if "Periodo:" in val:
                    period_str = val
                    break
            if period_str:
                break

        if not period_str:
            raise ValueError("No se encontró el periodo del reporte (ej. 'Periodo: 2026-08-01 ~ 2026-08-06') en el archivo Excel")

        dates = re.findall(r'\d{4}-\d{2}-\d{2}', period_str)
        if len(dates) == 2:
            start_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d").date()
        else:
            raise ValueError(f"No se pudo extraer el rango de fechas del periodo: {period_str}")

        # 3. Procesar las filas por docente
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        registros_procesados = 0

        try:
            r = 0
            while r < len(df):
                val_col0 = str(df.iloc[r, 0]).strip()
                if "ID:" in val_col0 or val_col0 == "ID":
                    # Extraer ID del docente de la columna 1 o 2 (índice 1 o 2)
                    teacher_id_raw = df.iloc[r, 1]
                    if pd.isna(teacher_id_raw) or str(teacher_id_raw).strip() == "":
                        teacher_id_raw = df.iloc[r, 2]
                    
                    try:
                        # Convertir primero a float y luego a int por si viene como "14.0" o similar
                        teacher_id = int(float(str(teacher_id_raw).strip()))
                    except ValueError:
                        try:
                            # Si tiene texto (ej: "ID: 14"), cortamos en el punto decimal primero
                            clean_str = str(teacher_id_raw).split('.')[0]
                            id_clean = "".join(re.findall(r'\d+', clean_str))
                            teacher_id = int(id_clean)
                        except ValueError:
                            teacher_id = None

                    if not teacher_id:
                        r += 1
                        continue

                    # Obtener los horarios de este docente registrados en el sistema
                    cursor.execute("""
                        SELECT 
                            h.diaSemana,
                            h.horaInicio,
                            h.horaFin,
                            g.fechaInicio,
                            g.fechaFin
                        FROM tb_horarios h
                        JOIN tb_grupos g ON h.id_grupo = g.id
                        WHERE h.id_docente = %s
                    """, (teacher_id,))
                    teacher_schedules = cursor.fetchall()

                    # La siguiente fila contiene los tiempos de asistencia diarios
                    r_times = r + 1
                    if r_times < len(df):
                        max_days = (end_date - start_date).days + 1
                        
                        for col_idx in range(min(max_days, len(df.columns))):
                            cell_value = df.iloc[r_times, col_idx]
                            
                            # Determinar la fecha exacta
                            day_num = col_idx + 1
                            try:
                                date_val = datetime.date(start_date.year, start_date.month, day_num)
                            except ValueError:
                                continue

                            # Mapeo de día de la semana
                            db_weekday = date_val.weekday() + 1

                            # Filtrar y deduplicar horarios del docente activos para esta fecha
                            slots_dia = []
                            for s in teacher_schedules:
                                h_fecha_inicio = s['fechaInicio']
                                h_fecha_fin = s['fechaFin']
                                if isinstance(h_fecha_inicio, datetime.datetime):
                                    h_fecha_inicio = h_fecha_inicio.date()
                                if isinstance(h_fecha_fin, datetime.datetime):
                                    h_fecha_fin = h_fecha_fin.date()
                                    
                                if s['diaSemana'] == db_weekday and h_fecha_inicio <= date_val <= h_fecha_fin:
                                    slots_dia.append(s)

                            # Agrupar por (horaInicio, horaFin) para deduplicar materias en el mismo horario
                            slots_dia_map = {}
                            for s in slots_dia:
                                key = (s['horaInicio'], s['horaFin'])
                                slots_dia_map[key] = s
                            slots_dia_dedup = list(slots_dia_map.values())

                            # Si el docente no tiene clases este día en el sistema, no lo registramos
                            if not slots_dia_dedup:
                                continue

                            # Parsear marcajes del docente en el Excel para este día
                            cell_str = str(cell_value).strip() if not pd.isna(cell_value) else ""
                            
                            # Separar los marcajes por salto de línea y DEDUPLICAR del mismo minuto usando set
                            times = [t.strip() for t in cell_str.split("\n") if t.strip()]
                            times = sorted(list(set(times)))

                            # Convertir los marcajes en objetos timedelta
                            check_tds = []
                            for t in times:
                                try:
                                    parts = t.split(':')
                                    h_val = int(parts[0])
                                    m_val = int(parts[1])
                                    check_tds.append(timedelta(hours=h_val, minutes=m_val))
                                except:
                                    continue
                            check_tds.sort()

                            # Agrupar los horarios en bloques contiguos de clase
                            class_intervals = []
                            for s in slots_dia_dedup:
                                start_td = s['horaInicio']
                                end_td = s['horaFin']
                                if isinstance(start_td, str):
                                    h_v, m_v, s_v = map(int, start_td.split(':'))
                                    start_td = timedelta(hours=h_v, minutes=m_v, seconds=s_v)
                                elif isinstance(start_td, datetime.time):
                                    start_td = timedelta(hours=start_td.hour, minutes=start_td.minute, seconds=start_td.second)
                                    
                                if isinstance(end_td, str):
                                    h_v, m_v, s_v = map(int, end_td.split(':'))
                                    end_td = timedelta(hours=h_v, minutes=m_v, seconds=s_v)
                                elif isinstance(end_td, datetime.time):
                                    end_td = timedelta(hours=end_td.hour, minutes=end_td.minute, seconds=end_td.second)
                                    
                                class_intervals.append((start_td, end_td))

                            class_intervals.sort(key=lambda x: x[0])
                            
                            blocks = []
                            for start, end in class_intervals:
                                if not blocks:
                                    blocks.append([start, end])
                                else:
                                    prev_start, prev_end = blocks[-1]
                                    if start <= prev_end:
                                        blocks[-1][1] = max(prev_end, end)
                                    else:
                                        blocks.append([start, end])

                            # Evaluar marcajes para cada bloque e intersecciones
                            real_minutos = 0.0
                            primer_marcaje_del_dia = None
                            ultimo_marcaje_del_dia = None
                            
                            all_missing_transitions = []
                            has_checks_any_block = False
                            retardos_lista = []
                            salidas_anticipadas_lista = []

                            for B_start, B_end in blocks:
                                # Ventana de tolerancia: +/- 45 minutos del bloque
                                block_checks = [t for t in check_tds if (B_start - timedelta(minutes=45)) <= t <= (B_end + timedelta(minutes=45))]
                                
                                if not block_checks:
                                    continue
                                
                                has_checks_any_block = True
                                t_in = block_checks[0]
                                t_out = block_checks[-1]
                                
                                if primer_marcaje_del_dia is None or t_in < primer_marcaje_del_dia:
                                    primer_marcaje_del_dia = t_in
                                if ultimo_marcaje_del_dia is None or t_out > ultimo_marcaje_del_dia:
                                    ultimo_marcaje_del_dia = t_out
                                    
                                # Calcular intersección
                                start_eff = max(B_start, t_in)
                                end_eff = min(B_end, t_out)
                                block_minutos = max(0.0, (end_eff - start_eff).total_seconds() / 60.0)
                                real_minutos += block_minutos
                                
                                # Evaluar retardo (> 5 minutos)
                                if t_in > (B_start + timedelta(minutes=5)):
                                    delay_mins = int((t_in - B_start).total_seconds() // 60)
                                    retardos_lista.append(f"{delay_mins} min")
                                    
                                # Evaluar salida anticipada (> 5 minutos)
                                if t_out < (B_end - timedelta(minutes=5)):
                                    early_mins = int((B_end - t_out).total_seconds() // 60)
                                    salidas_anticipadas_lista.append(f"{early_mins} min")

                                # Verificar marcajes en cada límite de clase dentro de este bloque
                                block_boundaries = set()
                                for start_td, end_td in class_intervals:
                                    if B_start <= start_td and end_td <= B_end:
                                        block_boundaries.add(start_td)
                                        block_boundaries.add(end_td)
                                block_boundaries = sorted(list(block_boundaries))
                                
                                for b in block_boundaries:
                                    has_check = any((b - timedelta(minutes=15)) <= t <= (b + timedelta(minutes=15)) for t in check_tds)
                                    if not has_check:
                                        all_missing_transitions.append(b)

                            if not has_checks_any_block:
                                hora_entrada_str = "00:00:00"
                                hora_salida_str = "00:00:00"
                                horas_trabajadas = 0.0
                                estado = "Falta"
                                observaciones = "No se registraron marcajes en las ventanas de clase del día."
                            else:
                                hora_entrada_str = str_from_td(primer_marcaje_del_dia)
                                hora_salida_str = str_from_td(ultimo_marcaje_del_dia)
                                horas_trabajadas = round(real_minutos / 60.0, 2)
                                
                                # Clasificar estado y observaciones
                                if all_missing_transitions:
                                    estado = "Advertencia"
                                    missing_strs = [str_from_td(b)[:5] for b in all_missing_transitions]
                                    observaciones = f"No registró por hora: faltan marcajes intermedios en transición(es) de las {', '.join(missing_strs)}."
                                elif retardos_lista or salidas_anticipadas_lista:
                                    estado = "Parcial/Retardo"
                                    obs_parts = []
                                    if retardos_lista:
                                        obs_parts.append(f"Retardo de {', '.join(retardos_lista)}")
                                    if salidas_anticipadas_lista:
                                        obs_parts.append(f"Salida anticipada de {', '.join(salidas_anticipadas_lista)}")
                                    observaciones = "; ".join(obs_parts)
                                else:
                                    estado = "Completo"
                                    observaciones = "Asistencia completa."

                            # Guardar en la base de datos
                            cursor.execute("""
                                INSERT INTO tb_asistencias_docentes 
                                    (id_docente, fecha, hora_entrada, hora_salida, horas_trabajadas, estado, observaciones)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                    hora_entrada = VALUES(hora_entrada),
                                    hora_salida = VALUES(hora_salida),
                                    horas_trabajadas = VALUES(horas_trabajadas),
                                    estado = VALUES(estado),
                                    observaciones = VALUES(observaciones)
                            """, (teacher_id, date_val.strftime("%Y-%m-%d"), hora_entrada_str, hora_salida_str, horas_trabajadas, estado, observaciones))
                            registros_procesados += 1

                    r += 2
                else:
                    r += 1
            
            conexion.commit()
            return registros_procesados

        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_asistencias(fecha_inicio_str, fecha_fin_str, id_docente=None):
        import datetime
        try:
            datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Las fechas deben tener el formato YYYY-MM-DD")

        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
                SELECT 
                    a.id,
                    a.id_docente,
                    CONCAT(d.nombreDocente, ' ', COALESCE(d.apPaternoDocente, ''), ' ', COALESCE(d.apMaternoDocente, '')) AS docente,
                    DATE_FORMAT(a.fecha, '%%Y-%%m-%%d') AS fecha,
                    TIME_FORMAT(a.hora_entrada, '%%H:%%i:%%s') AS hora_entrada,
                    TIME_FORMAT(a.hora_salida, '%%H:%%i:%%s') AS hora_salida,
                    a.horas_trabajadas,
                    a.estado,
                    a.observaciones
                FROM tb_asistencias_docentes a
                JOIN tb_docentes d ON a.id_docente = d.idDocente
                WHERE a.fecha BETWEEN %s AND %s
            """
            params = [fecha_inicio_str, fecha_fin_str]
            if id_docente:
                sql += " AND a.id_docente = %s"
                params.append(id_docente)

            sql += " ORDER BY a.fecha DESC, docente ASC"
            cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            for r in rows:
                if r['horas_trabajadas'] is not None:
                    h_val = float(r['horas_trabajadas'])
                    r['horas_trabajadas'] = int(h_val) if h_val.is_integer() else h_val

            return rows
        finally:
            cursor.close()
            conexion.close()
