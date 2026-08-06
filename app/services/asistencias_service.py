import os
import re
import datetime
from datetime import timedelta
import pandas as pd
import pymysql
from app.config.conexion import get_connection

class AsistenciasService:
    @staticmethod
    def procesar_excel(file_stream):
        # 1. Leer el archivo Excel en memoria usando pandas
        # Buscamos la hoja que contenga "asistencia" o "reporte" en su nombre.
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
        cursor = conexion.cursor()
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
                        # Extraer solo dígitos del ID por si viene con texto
                        id_clean = "".join(re.findall(r'\d+', str(teacher_id_raw)))
                        teacher_id = int(id_clean)
                    except ValueError:
                        teacher_id = None

                    # Nombre del docente (en columna K, índice 10)
                    teacher_name = str(df.iloc[r, 10]).strip() if len(df.columns) > 10 else ""

                    if not teacher_id:
                        r += 1
                        continue

                    # La siguiente fila contiene los tiempos de asistencia diarios
                    r_times = r + 1
                    if r_times < len(df):
                        # Las columnas desde la columna A (índice 0) hasta el final del periodo
                        max_days = (end_date - start_date).days + 1
                        
                        for col_idx in range(min(max_days, len(df.columns))):
                            cell_value = df.iloc[r_times, col_idx]
                            if pd.isna(cell_value):
                                continue
                            
                            cell_str = str(cell_value).strip()
                            if not cell_str:
                                continue

                            # Separar los marcajes por salto de línea
                            times = [t.strip() for t in cell_str.split("\n") if t.strip()]
                            if not times:
                                continue

                            # Determinar la fecha exacta
                            day_num = col_idx + 1
                            try:
                                date_val = datetime.date(start_date.year, start_date.month, day_num)
                            except ValueError:
                                continue # Día fuera de rango para ese mes

                            # Ordenar marcajes para obtener primer y último registro
                            times.sort()
                            hora_entrada = times[0]
                            hora_salida = times[-1]

                            # Calcular horas trabajadas
                            try:
                                t_ent = datetime.datetime.strptime(hora_entrada, "%H:%M" if len(hora_entrada) <= 5 else "%H:%M:%S")
                                t_sal = datetime.datetime.strptime(hora_salida, "%H:%M" if len(hora_salida) <= 5 else "%H:%M:%S")
                                diff_min = (t_sal - t_ent).total_seconds() / 60.0
                                horas_trabajadas = round(diff_min / 60.0, 2)
                            except ValueError:
                                horas_trabajadas = 0.0

                            # Guardar en la base de datos
                            cursor.execute("""
                                INSERT INTO tb_asistencias_docentes 
                                    (id_docente, fecha, hora_entrada, hora_salida, horas_trabajadas)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                    hora_entrada = VALUES(hora_entrada),
                                    hora_salida = VALUES(hora_salida),
                                    horas_trabajadas = VALUES(horas_trabajadas)
                            """, (teacher_id, date_val.strftime("%Y-%m-%d"), hora_entrada, hora_salida, horas_trabajadas))
                            registros_procesados += 1

                    # Avanzar a la siguiente sección (generalmente avanzamos 2 filas)
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
                    a.horas_trabajadas
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
