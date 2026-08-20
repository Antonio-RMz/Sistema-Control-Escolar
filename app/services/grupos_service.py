from app.config.conexion import get_connection
import datetime

class GruposService:
    @staticmethod
    # para obtener todos los grupos con búsqueda y paginación
    def get_all(page=1, limit=50, search="", id_centro_trabajo=None, id_nivel_academico=None, id_generacion=None, status_grupo=None, modalidad_horario=None, dia=None, id_docente=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Validaciones de entrada para consistencia
            if page < 1:
                page = 1
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200

            offset = (page - 1) * limit
            where_clauses = []
            params = []

            if id_docente:
                where_clauses.append("g.id IN (SELECT DISTINCT id_grupo FROM tb_horarios WHERE id_docente = %s)")
                params.append(id_docente)

            if search:
                where_clauses.append("g.clave LIKE %s")
                params.append(f"%{search}%")
            if id_centro_trabajo:
                where_clauses.append("g.id_centroTrabajo = %s")
                params.append(id_centro_trabajo)
            if id_nivel_academico:
                where_clauses.append("g.id_nivel_academico = %s")
                params.append(id_nivel_academico)
            if id_generacion:
                where_clauses.append("g.idGeneracion = %s")
                params.append(id_generacion)
            if status_grupo:
                where_clauses.append("g.statusGrupo = %s")
                params.append(status_grupo)
            if modalidad_horario:
                modalidad_upper = str(modalidad_horario).strip().upper()
                if "MATUTINO" in modalidad_upper:
                    where_clauses.append("""(
                        g.modalidadHorario LIKE %s 
                        OR g.modalidadHorario LIKE %s 
                        OR g.modalidadHorario LIKE %s
                    )""")
                    params.extend(["%MATUTINO%", "%MAÑANA%", "%MANANA%"])
                elif "VESPERTINO" in modalidad_upper:
                    where_clauses.append("""(
                        g.modalidadHorario LIKE %s 
                        OR g.modalidadHorario LIKE %s
                    )""")
                    params.extend(["%VESPERTINO%", "%TARDE%"])
                else:
                    where_clauses.append("g.modalidadHorario LIKE %s")
                    params.append(f"%{modalidad_horario}%")
            if dia:
                dia_upper = str(dia).strip().upper()
                if any(x in dia_upper for x in ["LUNES", "VIERNES", "ESCOLARIZADO", "LV"]):
                    where_clauses.append("""(
                        gd.dia LIKE %s OR gd.dia LIKE %s OR gd.dia = %s
                        OR g.clave LIKE %s OR g.clave LIKE %s 
                        OR c.nombre LIKE %s OR c.nombre LIKE %s
                    )""")
                    params.extend([
                        "%LUNES%", "%VIERNES%", "LUNES-VIERNES",
                        "BTI%", "%LV%",
                        "%BTI%", "%COMPUTACION%"
                    ])
                elif "SAB" in dia_upper or dia_upper == "S":
                    where_clauses.append("""(
                        gd.dia LIKE %s OR gd.dia = %s
                        OR ((g.clave LIKE %s OR g.clave LIKE %s) AND g.clave NOT LIKE %s AND g.clave NOT LIKE %s)
                    )""")
                    params.extend([
                        "%SAB%", "SABADO",
                        "%S", "%SAB%", "%LV%", "BTI%"
                    ])
                elif "DOM" in dia_upper or dia_upper == "D":
                    where_clauses.append("""(
                        gd.dia LIKE %s OR gd.dia = %s
                        OR ((g.clave LIKE %s OR g.clave LIKE %s) AND g.clave NOT LIKE %s)
                    )""")
                    params.extend([
                        "%DOM%", "DOMINGO",
                        "%D", "%DOM%", "BTI%"
                    ])
                else:
                    where_clauses.append("(gd.dia LIKE %s OR g.clave LIKE %s)")
                    params.extend([f"%{dia}%", f"%{dia}%"])

            where = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            # Obtener el total para la paginación
            sql_total = f"""
                SELECT COUNT(DISTINCT g.id) AS total 
                FROM tb_grupos g 
                LEFT JOIN tb_centrotrabajo c ON g.id_centroTrabajo = c.id
                LEFT JOIN tb_grupodias gd ON g.id = gd.idGrupo
                {where}
            """
            cursor.execute(sql_total, params)
            total = cursor.fetchone()["total"]

            # Obtener los datos paginados
            sql_datos = f"""
                SELECT 
                    g.id, 
                    g.clave, 
                    g.fechaCreacion, 
                    g.fechaInicio, 
                    g.fechaFin,
                    g.id_centroTrabajo, 
                    c.nombre AS nombreCentroTrabajo,
                    g.id_tipoPeriodo, 
                    tp.nombrePeriodo,
                    g.id_planEstudios, 
                    g.id_nivel_academico,
                    n.nombre AS nombre_nivel,
                    g.idGeneracion,
                    gen.nombreGeneracion,
                    gen.generacion AS numeroGeneracion,
                    g.modalidadHorario,
                    g.statusGrupo,
                    IFNULL(GROUP_CONCAT(gd.dia), '') AS diasClase,
                    (SELECT COUNT(*) FROM tb_alumnogrupo WHERE idGrupo = g.id AND estado = 'ACTIVO') AS alumnos_count,
                    (SELECT aula FROM tb_horarios WHERE id_grupo = g.id LIMIT 1) AS aula
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo c ON g.id_centroTrabajo = c.id
                LEFT JOIN tb_tipoperiodo tp ON g.id_tipoPeriodo = tp.id
                LEFT JOIN tb_niveles_academicos n ON g.id_nivel_academico = n.id
                LEFT JOIN tb_generaciones gen ON g.idGeneracion = gen.id
                LEFT JOIN tb_grupodias gd ON g.id = gd.idGrupo
                {where}
                GROUP BY g.id
                ORDER BY g.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, params + [limit, offset])
            data = cursor.fetchall()
            
            for row in data:
                dias_str = row.get("diasClase")
                dias_list = dias_str.split(",") if dias_str else []
                if not dias_list:
                    modalidad = (row.get("modalidadHorario") or "").upper()
                    if "SABADO" in modalidad or "SÁBADO" in modalidad:
                        dias_list = ["SABADO"]
                    elif "DOMINGO" in modalidad:
                        dias_list = ["DOMINGO"]
                    elif "MATUTINO" in modalidad or "VESPERTINO" in modalidad:
                        dias_list = ["LUNES-VIERNES"]
                    else:
                        clave = (row.get("clave") or "").upper()
                        if clave.endswith("S"):
                            dias_list = ["SABADO"]
                        elif clave.endswith("D"):
                            dias_list = ["DOMINGO"]
                        elif "LV" in clave or "BTI" in clave:
                            dias_list = ["LUNES-VIERNES"]
                        else:
                            if row.get("id_centroTrabajo") == 2:
                                dias_list = ["LUNES-VIERNES"]
                            else:
                                dias_list = ["SABADO"]
                row["diasClase"] = dias_list
                
                try:
                    from app.services.periodos_academico import PeriodoAcademicoService
                    res_nivel = PeriodoAcademicoService.calcularNivelGrupo(row["id"])
                    if res_nivel:
                        # Convert to string to ensure clean JSON serialization in Flask
                        row["fechaInicioNivel"] = str(res_nivel.get("fechaInicioNivel")) if res_nivel.get("fechaInicioNivel") else None
                        row["fechaFinNivel"] = str(res_nivel.get("fechaFinNivel")) if res_nivel.get("fechaFinNivel") else None
                except Exception as ex:
                    print("Error al calcular nivel del grupo:", ex)

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "search": search,
                "data": data,
            }
        finally:
            cursor.close()
            conexion.close()

    # para crear los grupos
    @staticmethod
    def create(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            fecha_inicio_str = data.get("fechaInicio")
            fecha_fin = data.get("fechaFin")
            duracion_semanas = data.get("duracionSemanas")
            
            if duracion_semanas and fecha_inicio_str:
                # Calcular fechaFin sumando semanas
                fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
                fecha_fin_dt = fecha_inicio_dt + datetime.timedelta(weeks=int(duracion_semanas))
                fecha_fin = fecha_fin_dt.strftime("%Y-%m-%d")

            query = """
                INSERT INTO tb_grupos (
                    clave, fechaCreacion, fechaInicio, fechaFin, 
                    id_centroTrabajo, id_tipoPeriodo, id_planEstudios, modalidadHorario, id_nivel_academico,statusGrupo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data.get("clave"),
                data.get("fechaCreacion"),
                fecha_inicio_str,
                fecha_fin,
                data.get("id_centroTrabajo"),
                data.get("id_tipoPeriodo"),
                data.get("id_planEstudios"),
                data.get("modalidadHorario"),
                data.get("id_nivel_academico"),
                data.get("statusGrupo")
            )
            cursor.execute(query, values)
            
            id_grupo = cursor.lastrowid
            
            # Guardar los días de clase si vienen en el payload
            dias_clase = data.get("diasClase", [])
            if dias_clase:
                query_dias = "INSERT INTO tb_grupodias (idGrupo, dia) VALUES (%s, %s)"
                for dia in dias_clase:
                    cursor.execute(query_dias, (id_grupo, dia))
                    
            conexion.commit()
            return {"mensaje": "Grupo creado correctamente", "idGrupo": id_grupo}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
#para obtener los alumnos por grupo
    @staticmethod
    def get_alumnos_by_grupo(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT a.*
                FROM tb_alumnos a
                INNER JOIN tb_alumnogrupo ag 
                    ON a.idAlumno = ag.idAlumno
                WHERE ag.idGrupo = %s
            """
            cursor.execute(query, (id_grupo,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()
   #para actualizar los datos de un grupo
    @staticmethod
    def update(id_grupo, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            fecha_inicio_str = data.get("fechaInicio")
            fecha_fin = data.get("fechaFin")

            query = """
                UPDATE tb_grupos 
                SET
                    clave = %s,
                    fechaCreacion = %s,
                    fechaInicio = %s,
                    fechaFin = %s,
                    id_centroTrabajo = %s,
                    id_tipoPeriodo = %s,
                    id_planEstudios = %s,
                    modalidadHorario = %s,
                    id_nivel_academico = %s,
                    statusGrupo = %s
                WHERE id = %s
            """
            values = (
                data.get("clave"),
                data.get("fechaCreacion"),
                fecha_inicio_str,
                fecha_fin,
                data.get("id_centroTrabajo"),
                data.get("id_tipoPeriodo"),
                data.get("id_planEstudios"),
                data.get("modalidadHorario"),
                data.get("id_nivel_academico"),
                data.get("statusGrupo"),
                id_grupo
            )
            cursor.execute(query, values)
            
            # Actualizar días de clase si vienen en el payload
            dias_clase = data.get("diasClase", [])
            if dias_clase:
                cursor.execute("DELETE FROM tb_grupodias WHERE idGrupo = %s", (id_grupo,))
                query_dias = "INSERT INTO tb_grupodias (idGrupo, dia) VALUES (%s, %s)"
                for dia in dias_clase:
                    cursor.execute(query_dias, (id_grupo, dia))

            conexion.commit()
            return {"mensaje": "Grupo actualizado correctamente", "idGrupo": id_grupo}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    #para obtener la informacion de un solo grupo
    def get_grupo(id_grupo):
        import pymysql
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            query = """
                SELECT g.*, n.nombre AS nombre_nivel
                FROM tb_grupos g
                LEFT JOIN tb_niveles_academicos n ON g.id_nivel_academico = n.id
                WHERE g.id = %s
            """
            cursor.execute(query, (id_grupo,))
            grupo = cursor.fetchone()
            
            if grupo:
                try:
                    from app.services.periodos_academico import PeriodoAcademicoService
                    periodo_info = PeriodoAcademicoService.calcularNivelGrupo(id_grupo)
                    if periodo_info:
                        # Convertir fechas a string para serialización JSON segura
                        grupo["fechaInicioNivel"] = periodo_info["fechaInicioNivel"].strftime("%Y-%m-%d") if isinstance(periodo_info["fechaInicioNivel"], datetime.date) else periodo_info["fechaInicioNivel"]
                        grupo["fechaFinNivel"] = periodo_info["fechaFinNivel"].strftime("%Y-%m-%d") if isinstance(periodo_info["fechaFinNivel"], datetime.date) else periodo_info["fechaFinNivel"]
                except Exception as e:
                    print(f"Error calculating level period: {e}")
                    
            return grupo
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete(id_grupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Desvincular alumnos en tb_alumnos (poner idGrupo = NULL)
            cursor.execute("UPDATE tb_alumnos SET idGrupo = NULL WHERE idGrupo = %s", (id_grupo,))
            # 2. Eliminar días del grupo
            cursor.execute("DELETE FROM tb_grupodias WHERE idGrupo = %s", (id_grupo,))
            # 3. Eliminar relación alumno-grupo en tb_alumnogrupo
            cursor.execute("DELETE FROM tb_alumnogrupo WHERE idGrupo = %s", (id_grupo,))
            # 4. Eliminar horarios del grupo
            cursor.execute("DELETE FROM tb_horarios WHERE id_grupo = %s", (id_grupo,))
            # 5. Eliminar el grupo
            cursor.execute("DELETE FROM tb_grupos WHERE id = %s", (id_grupo,))
            
            conexion.commit()
            return {"mensaje": "Grupo eliminado correctamente", "idGrupo": id_grupo}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
    