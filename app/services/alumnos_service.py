from app.config.conexion import get_connection
import pandas as pd
import math


class AlumnosService:
    @staticmethod
    def get_alumnos(page=1, limit=50, generacion=None, idGrupo=None, search="", id_centro_trabajo=None, status_alumno=None, modalidad_estudio=None, order="ASC"):
        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            if page < 1:
                page = 1
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200

            offset = (page - 1) * limit
            where = []
            valores = []

            if generacion:
                where.append("g.generacion = %s")
                valores.append(generacion)

            if idGrupo:
                where.append("a.idGrupo = %s")
                valores.append(idGrupo)

            if id_centro_trabajo:
                where.append("gr.id_centroTrabajo = %s")
                valores.append(id_centro_trabajo)

            if status_alumno:
                where.append("a.statusAlumno = %s")
                valores.append(status_alumno)

            if modalidad_estudio:
                where.append("a.modalidad_estudio = %s")
                valores.append(modalidad_estudio)

            if search:
                palabras = search.strip().split()

                for palabra in palabras:
                    where.append(
                        "(a.nombre LIKE %s OR a.apPaterno LIKE %s OR a.apMaterno LIKE %s OR gr.clave LIKE %s OR a.numeroControl LIKE %s)"
                    )

                    like = f"%{palabra}%"
                    valores.extend([like, like, like, like, like])

            where_sql = "WHERE " + " AND ".join(where) if where else ""

            # Total de registros
            sql_total = f"""
                SELECT COUNT(*) AS total
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                {where_sql}
            """

            cursor.execute(sql_total, valores)
            total = cursor.fetchone()["total"]

            # Sanear ordenación
            order_direction = "DESC" if str(order).upper() == "DESC" else "ASC"

            # Consulta paginada
            sql_datos = f"""
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.fechaNacimiento,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    g.generacion AS nombreGeneracionTexto,
                    gr.clave AS nombreGrupoTexto,
                    d.calle,
                    d.colonia,
                    d.localidad,
                    d.municipio,
                    d.numeroExterior,
                    d.numeroInterior,
                    cert.folioCertificado,
                    cert.recogioCertificado,
                    cert.fechaRecogioCertificado,
                    CONCAT_WS(' ', c.nombre, c.apPaterno, c.apMaterno) AS tutor,
                    ac.parentesco,
                    COALESCE(c.telefono, c.celular) AS telefonoTutor,
                    COALESCE(a.modalidad_estudio, 'PRESENCIAL') AS modalidad_estudio,
                    COALESCE(a.dia_pago, 'SABADO') AS dia_pago,
                    a.moodle_user_id,
                    a.moodle_username,
                    a.moodle_password,
                    COALESCE(a.semana_actual_pagada, 0) AS semana_actual_pagada,
                    a.fecha_proximo_pago
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_direcciones_alumno d ON a.idAlumno = d.idAlumno
                LEFT JOIN tb_certificados_alumno cert ON a.idAlumno = cert.idAlumno
                LEFT JOIN tb_alumno_contacto ac ON ac.id = (
                    SELECT MIN(ac2.id) FROM tb_alumno_contacto ac2 
                    WHERE ac2.idAlumno = a.idAlumno AND (ac2.esTutor = 1 OR ac2.esPrincipal = 1)
                )
                LEFT JOIN tb_contactos c ON ac.idContacto = c.idContacto
                {where_sql}
                ORDER BY a.idAlumno {order_direction}
                LIMIT %s OFFSET %s
            """

            cursor.execute(sql_datos, valores + [limit, offset])
            alumnos = cursor.fetchall()

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "search": search,
                "data": alumnos,
            }

        finally:
            cursor.close()
            conexion.close()
    ## CREAR ALUMNO - NUEVO FLUJO DINÁMICO CON VALIDACIONES V1-V8
    @staticmethod
    def create_alumno(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Normalizar payload (soporta formato estructurado o plano)
            alumno_data = data.get("alumno") if isinstance(data.get("alumno"), dict) else data
            academico_data = data.get("academico") if isinstance(data.get("academico"), dict) else data
            equiv_data = data.get("equivalencia") if isinstance(data.get("equivalencia"), dict) else {}

            nombre = (alumno_data.get("nombre") or "").strip()
            ap_paterno = (alumno_data.get("apPaterno") or "").strip() or None
            ap_materno = (alumno_data.get("apMaterno") or "").strip() or None
            curp = (alumno_data.get("curp") or "").strip() or None
            fecha_nacimiento = alumno_data.get("fechaNacimiento") or None
            celular_alumno = alumno_data.get("celularAlumno") or None
            correo_alumno = alumno_data.get("correoAlumno") or None
            escuela_procedencia = alumno_data.get("escuelaProcedencia") or None
            observaciones = alumno_data.get("observaciones") or None
            numero_control = alumno_data.get("numeroControl") or None
            status_alumno = alumno_data.get("statusAlumno") or "ACTIVO"
            create_by = data.get("createBy") or alumno_data.get("createBy")

            # Equivalencia
            equivalencia = (
                equiv_data.get("requiereEquivalencia") 
                if "requiereEquivalencia" in equiv_data 
                else alumno_data.get("equivalencia")
            )
            if isinstance(equivalencia, bool):
                equivalencia = "SI" if equivalencia else "NO"
            elif isinstance(equivalencia, int):
                equivalencia = "SI" if equivalencia == 1 else "NO"
            else:
                equivalencia = "SI" if str(equivalencia).upper() in ["SI", "1", "TRUE", "SÍ"] else "NO"

            # Documentos y Pagos
            certificado_incompleto = (
                "SI" if equiv_data.get("cuentaConCertificadoIncompleto") == True or str(equiv_data.get("cuentaConCertificadoIncompleto")).upper() in ["SI", "1", "TRUE"]
                else ("NO" if "cuentaConCertificadoIncompleto" in equiv_data else (alumno_data.get("certificado_incompleto") or "NO"))
            )
            if isinstance(certificado_incompleto, bool):
                certificado_incompleto = "SI" if certificado_incompleto else "NO"
            else:
                certificado_incompleto = "SI" if str(certificado_incompleto).upper() in ["SI", "1", "TRUE", "SÍ"] else "NO"

            fecha_entrega_certificado = equiv_data.get("fechaEntrega") or alumno_data.get("fecha_entrega_certificado") or None
            
            trae_boleta = data.get("traeBoleta") or alumno_data.get("trae_boleta") or "SI"
            if isinstance(trae_boleta, bool):
                trae_boleta = "SI" if trae_boleta else "NO"
            else:
                trae_boleta = "SI" if str(trae_boleta).upper() in ["SI", "1", "TRUE", "SÍ"] else "NO"
            
            estado_pago_equivalencia = equiv_data.get("estadoPago") or alumno_data.get("estado_pago_equivalencia") or "PENDIENTE"

            # Datos académicos
            id_centro_trabajo = academico_data.get("idCentroTrabajo") or academico_data.get("id_centroTrabajo")
            id_nivel_academico = academico_data.get("idNivelAcademico") or academico_data.get("id_nivel_academico") or academico_data.get("idPeriodo")
            id_generacion = academico_data.get("idGeneracion") or academico_data.get("id_generacion")
            id_grupo = academico_data.get("idGrupo") or academico_data.get("id_grupo")

            # Check if it is a historical record
            es_historico = observaciones and "[REGISTRO_HISTORICO]" in observaciones

            # Validación requeridos básicos de alumno
            if not nombre:
                return {"error": "El nombre del alumno es obligatorio."}, 400

            if not es_historico and not ap_paterno:
                return {"error": "El apellido paterno del alumno es obligatorio."}, 400

            # --- VALIDACIÓN 1: CCT existente ---
            id_programa = None
            cct_tipo_periodo = None
            if id_centro_trabajo:
                cursor.execute(
                    "SELECT id, nombre, idPrograma, idTipoPeriodo FROM tb_centrotrabajo WHERE id = %s",
                    (id_centro_trabajo,)
                )
                cct_row = cursor.fetchone()
                if not cct_row:
                    return {"error": f"El Centro de Trabajo con ID {id_centro_trabajo} no existe."}, 400
                id_programa = cct_row.get("idPrograma")
                cct_tipo_periodo = cct_row.get("idTipoPeriodo")

            # --- VALIDACIÓN 2: Programa asociado válido ---
            if id_programa:
                cursor.execute(
                    "SELECT id, nombrePrograma FROM tb_programas WHERE id = %s",
                    (id_programa,)
                )
                prog_row = cursor.fetchone()
                if not prog_row:
                    return {"error": f"El programa asociado (ID {id_programa}) no existe en el catálogo de programas."}, 400

            # --- VALIDACIÓN 3: Periodo / Nivel Académico corresponde al CCT ---
            if id_nivel_academico:
                cursor.execute(
                    "SELECT id, nombre, tipo, id_tipoPeriodo FROM tb_niveles_academicos WHERE id = %s",
                    (id_nivel_academico,)
                )
                nivel_row = cursor.fetchone()
                if not nivel_row:
                    return {"error": f"El nivel académico con ID {id_nivel_academico} no existe."}, 400
                
                if not es_historico and cct_tipo_periodo and nivel_row.get("id_tipoPeriodo") and int(nivel_row.get("id_tipoPeriodo")) != int(cct_tipo_periodo):
                    return {
                        "error": f"El nivel académico '{nivel_row.get('nombre')}' no es compatible con el esquema de periodicidad del Centro de Trabajo seleccionado."
                    }, 400

            # --- VALIDACIÓN 4 & 5: Grupo compatible con CCT y Nivel ---
            if id_grupo:
                cursor.execute(
                    "SELECT id, clave, id_centroTrabajo, id_tipoPeriodo, id_nivel_academico, idGeneracion FROM tb_grupos WHERE id = %s",
                    (id_grupo,)
                )
                grupo_row = cursor.fetchone()
                if not grupo_row:
                    return {"error": f"El grupo con ID {id_grupo} no existe."}, 400

                if id_centro_trabajo and grupo_row.get("id_centroTrabajo") and int(grupo_row["id_centroTrabajo"]) != int(id_centro_trabajo):
                    return {"error": "El grupo seleccionado no pertenece al Centro de Trabajo indicado."}, 400

                if not es_historico and id_nivel_academico and grupo_row.get("id_nivel_academico") and int(grupo_row["id_nivel_academico"]) != int(id_nivel_academico):
                    return {"error": "El grupo seleccionado no corresponde al nivel académico seleccionado."}, 400

                # Si no se pasó idGeneracion explícito pero el grupo tiene uno, tomar la del grupo
                if not id_generacion and grupo_row.get("idGeneracion"):
                    id_generacion = grupo_row.get("idGeneracion")

            # --- VALIDACIÓN 6: Generación existente ---
            if id_generacion:
                cursor.execute(
                    "SELECT id, nombreGeneracion FROM tb_generaciones WHERE id = %s",
                    (id_generacion,)
                )
                gen_row = cursor.fetchone()
                if not gen_row:
                    return {"error": f"La generación con ID {id_generacion} no existe."}, 400

            # --- VALIDACIÓN 8: Multi-trayectoria / Alumno existente ---
            id_alumno = None
            es_nuevo_alumno = True

            if curp:
                cursor.execute(
                    "SELECT idAlumno, nombre, apPaterno, apMaterno FROM tb_alumnos WHERE curp = %s",
                    (curp,)
                )
                alumno_existente = cursor.fetchone()
                if alumno_existente:
                    id_alumno = alumno_existente["idAlumno"]
                    es_nuevo_alumno = False

            if not id_alumno:
                # Insertar en tb_alumnos
                query_alumno = """
                    INSERT INTO tb_alumnos (
                        nombre, apPaterno, apMaterno, fechaNacimiento, celularAlumno,
                        correoAlumno, escuelaProcedencia, observaciones, idGeneracion,
                        idGrupo, equivalencia, numeroControl, statusAlumno, curp, createBy, id_nivel_ingreso,
                        certificado_incompleto, fecha_entrega_certificado, trae_boleta, estado_pago_equivalencia
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query_alumno,
                    (
                        nombre,
                        ap_paterno,
                        ap_materno,
                        fecha_nacimiento,
                        celular_alumno,
                        correo_alumno,
                        escuela_procedencia,
                        observaciones,
                        id_generacion,
                        id_grupo,
                        equivalencia,
                        numero_control,
                        status_alumno,
                        curp,
                        create_by,
                        id_nivel_academico,
                        certificado_incompleto,
                        fecha_entrega_certificado,
                        trae_boleta,
                        estado_pago_equivalencia,
                    ),
                )
                id_alumno = cursor.lastrowid
            else:
                # Alumno existente: actualizar campos complementarios si se proporcionaron
                update_fields = []
                update_values = []
                if celular_alumno:
                    update_fields.append("celularAlumno = %s")
                    update_values.append(celular_alumno)
                if correo_alumno:
                    update_fields.append("correoAlumno = %s")
                    update_values.append(correo_alumno)
                if update_fields:
                    update_values.append(id_alumno)
                    cursor.execute(
                        f"UPDATE tb_alumnos SET {', '.join(update_fields)} WHERE idAlumno = %s",
                        update_values
                    )

            # --- INSERTAR TRAYECTORIA EN tb_alumnoprograma ---
            id_alumno_programa = None
            if id_programa:
                cursor.execute(
                    "SELECT idAlumnoPrograma, estatusAlumnoPrograma FROM tb_alumnoprograma WHERE idAlumno = %s AND idPrograma = %s",
                    (id_alumno, id_programa)
                )
                prog_reg = cursor.fetchone()
                if not prog_reg:
                    cursor.execute(
                        """
                        INSERT INTO tb_alumnoprograma (
                            idAlumno, idPrograma, fechaInscripcion, estatusAlumnoPrograma, createBy
                        )
                        VALUES (%s, %s, CURRENT_DATE, 'INSCRITO', %s)
                        """,
                        (id_alumno, id_programa, create_by)
                    )
                    id_alumno_programa = cursor.lastrowid
                else:
                    id_alumno_programa = prog_reg["idAlumnoPrograma"]

            # --- INSERTAR RELACIÓN EN tb_alumnogrupo (si hay grupo) ---
            id_alumno_grupo = None
            if id_grupo:
                cursor.execute(
                    "SELECT id, estado FROM tb_alumnogrupo WHERE idAlumno = %s AND idGrupo = %s AND estado = 'ACTIVO'",
                    (id_alumno, id_grupo)
                )
                ag_reg = cursor.fetchone()
                if not ag_reg:
                    cursor.execute(
                        """
                        INSERT INTO tb_alumnogrupo (
                            idAlumno, idGrupo, fechaInicio, estado, createBy
                        )
                        VALUES (%s, %s, CURRENT_DATE, 'ACTIVO', %s)
                        """,
                        (id_alumno, id_grupo, create_by)
                    )
                    id_alumno_grupo = cursor.lastrowid
                else:
                    id_alumno_grupo = ag_reg["id"]

            # Cursos extracurriculares si vienen en el payload
            cursos = data.get("cursos") or alumno_data.get("cursos")
            if cursos and isinstance(cursos, list):
                query_cursos = """
                    INSERT INTO tb_cursoextraalumno (
                        idCursoExtracurricular, idAlumno, createDate, lastUpdateDate
                    ) VALUES (%s, %s, NOW(), NOW())
                """
                for id_curso in cursos:
                    cursor.execute(query_cursos, (id_curso, id_alumno))

            conexion.commit()
            return {
                "success": True,
                "mensaje": "Alumno y trayectoria académica registrados correctamente" if es_nuevo_alumno else "Trayectoria académica agregada al alumno existente",
                "idAlumno": id_alumno,
                "idPrograma": id_programa,
                "idAlumnoPrograma": id_alumno_programa,
                "idGrupo": id_grupo,
                "idAlumnoGrupo": id_alumno_grupo,
                "esNuevoAlumno": es_nuevo_alumno,
            }, 201
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}, 500
        finally:
            cursor.close()
            conexion.close()
#PARA IMPORTAR ALUMNOS
    @staticmethod
    def importar_alumnos_hoja(
        sheet_index=37,
        id_generacion=38,
        filename="scripts/GENERACIONES BTI 2026-2018.xlsx",
    ):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # Leer la hoja indicada
            df = pd.read_excel(filename, sheet_name=sheet_index)

            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip()

            insertados = 0
            for index, row in df.iterrows():
                # Helper para buscar columnas con nombres variados
                def get_val(names):
                    for name in names:
                        # Buscar en las columnas del row (ignorando espacios y mayúsculas)
                        for col in row.index:
                            if str(col).strip().upper() == name.strip().upper():
                                return row[col]
                    return None

                nombre = get_val(["nombre", "NOMBRE(S)", "NOMBRE"])
                apPaterno = get_val(["apPaterno", "APELLIDO PATERNO", "PATERNO"])
                apMaterno = get_val(["apMaterno", "APELLIDO MATERNO", "MATERNO"])
                n_control = get_val(
                    ["numeroControl", "NUMERO CONTROL", "NM. CONTROL", "NÚM. CONTROL"]
                )

                # Saltar filas vacías
                if pd.isna(nombre) and pd.isna(apPaterno):
                    continue

                query = """
                INSERT INTO tb_alumnos (
                    nombre, apPaterno, apMaterno, idGeneracion, fechaNacimiento,
                    tutor, parentesco, calle, colonia, localidad, municipio,
                    telefonoTutor, celularAlumno, correoAlumno, escuelaProcedencia,
                    observaciones, numeroControl
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                def f(val):
                    if pd.isna(val) or val is None:
                        return None
                    if isinstance(val, (float, int)):
                        # Validar que no sea infinito o NaN antes de convertir a int
                        if not math.isfinite(val):
                            return None
                        return str(int(val)).strip()
                    return str(val).strip()

                valores = (
                    f(nombre),
                    f(apPaterno),
                    f(apMaterno),
                    id_generacion,
                    f(row.get("fechaNacimiento")),
                    f(row.get("tutor")),
                    f(row.get("parentesco")),
                    f(row.get("calle")),
                    f(row.get("colonia")),
                    f(row.get("localidad")),
                    f(row.get("municipio")),
                    f(row.get("telefonoTutor")),
                    f(row.get("celularAlumno")),
                    f(row.get("correoAlumno")),
                    f(row.get("escuelaProcedencia")),
                    f(row.get("observaciones")),
                    f(n_control),
                )

                cursor.execute(query, valores)
                insertados += 1

            conexion.commit()
            return {
                "mensaje": "Alumnos importados correctamente",
                "total_insertados": insertados,
            }
        finally:
            cursor.close()
            conexion.close()

    # pendiente api para eliminar
    @staticmethod
    def delete_alumno(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            # 1. Eliminar asistencias
            cursor.execute(
                "DELETE FROM tb_asistencias_alumnos WHERE id_alumno = %s", (id_alumno,)
            )

            # 2. Eliminar justificaciones
            cursor.execute(
                "DELETE FROM tb_justificaciones_alumnos WHERE id_alumno = %s", (id_alumno,)
            )

            # 3. Eliminar calificaciones
            cursor.execute(
                "DELETE FROM tb_calificaciones WHERE idAlumno = %s", (id_alumno,)
            )

            # 4. Eliminar certificados
            cursor.execute(
                "DELETE FROM tb_certificados_alumno WHERE idAlumno = %s", (id_alumno,)
            )

            # 5. Eliminar direcciones
            cursor.execute(
                "DELETE FROM tb_direcciones_alumno WHERE idAlumno = %s", (id_alumno,)
            )

            # 6. Eliminar contactos del alumno
            cursor.execute(
                "DELETE FROM tb_alumno_contacto WHERE idAlumno = %s", (id_alumno,)
            )

            # 7. Eliminar contactos_alumno
            cursor.execute(
                "DELETE FROM tb_contactos_alumno WHERE idAlumno = %s", (id_alumno,)
            )

            # 8. Eliminar cursos extracurriculares
            cursor.execute(
                "DELETE FROM tb_cursoextraalumno WHERE idAlumno = %s", (id_alumno,)
            )

            # 9. Eliminar relación alumno-grupo
            cursor.execute(
                "DELETE FROM tb_alumnogrupo WHERE idAlumno = %s", (id_alumno,)
            )

            # 10. Eliminar relación alumno-programa
            cursor.execute(
                "DELETE FROM tb_alumnoprograma WHERE idAlumno = %s", (id_alumno,)
            )

            # 11. Eliminar alumno de la tabla principal
            cursor.execute("DELETE FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))

            conexion.commit()

            return {"mensaje": "Alumno eliminado correctamente", "idAlumno": id_alumno}, 200

        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}, 500

        finally:
            cursor.close()
            conexion.close()
    # PARA TRAERSE DETALLES DE UN ALUMNO
    @staticmethod
    def get_alumno(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            sql = """
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.fechaNacimiento,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    a.id_nivel_ingreso,
                    a.certificado_incompleto,
                    a.fecha_entrega_certificado,
                    a.trae_boleta,
                    a.estado_pago_equivalencia,
                    COALESCE(a.id_nivel_ingreso, gr.id_nivel_academico) AS idNivelAcademico,
                    COALESCE(a.id_nivel_ingreso, gr.id_nivel_academico) AS id_nivel_academico,
                    COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo) AS id_centroTrabajo,
                    COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo) AS idCentroTrabajo,
                    gr.id_nivel_academico,
                    gr.modalidadHorario AS jornadaHorario,
                    gr.fechaInicio AS fechaInicioGrupo,
                    g.generacion AS nombreGeneracionTexto,
                    g.nombreGeneracion,
                    gr.clave AS nombreGrupoTexto,
                    d.calle,
                    d.colonia,
                    d.localidad,
                    d.municipio,
                    d.numeroExterior,
                    d.numeroInterior,
                    d.estado AS estadoDireccion,
                    d.codigoPostal,
                    cert.folioCertificado,
                    cert.recogioCertificado,
                    cert.fechaRecogioCertificado,
                    cert.estadoCertificado,
                    cert.fechaEmision AS fechaEmisionCertificado,
                    CONCAT_WS(' ', c.nombre, c.apPaterno, c.apMaterno) AS tutor,
                    ac.parentesco,
                    COALESCE(c.telefono, c.celular) AS telefonoTutor,
                    COALESCE(a.modalidad_estudio, 'PRESENCIAL') AS modalidad_estudio,
                    COALESCE(a.dia_pago, 'SABADO') AS dia_pago,
                    a.moodle_user_id,
                    a.moodle_username,
                    a.moodle_password,
                    COALESCE(a.semana_actual_pagada, 0) AS semana_actual_pagada,
                    a.fecha_proximo_pago
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_direcciones_alumno d ON a.idAlumno = d.idAlumno
                LEFT JOIN tb_certificados_alumno cert ON a.idAlumno = cert.idAlumno
                LEFT JOIN tb_alumno_contacto ac ON ac.id = (
                    SELECT MIN(ac2.id) FROM tb_alumno_contacto ac2 
                    WHERE ac2.idAlumno = a.idAlumno AND (ac2.esTutor = 1 OR ac2.esPrincipal = 1)
                )
                LEFT JOIN tb_contactos c ON ac.idContacto = c.idContacto
                WHERE a.idAlumno = %s
            """
            cursor.execute(sql, (id_alumno,))
            alumno = cursor.fetchone()
            return {"data": alumno}
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    # PARA ACTUALIZAR ALUMNOS
    @staticmethod
    def update_alumno(id_alumno, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Actualizar tb_alumnos
            query = """
                UPDATE tb_alumnos 
                SET
                    nombre = %s,
                    apPaterno = %s,
                    apMaterno = %s,
                    fechaNacimiento = %s,
                    celularAlumno = %s,
                    correoAlumno = %s,
                    escuelaProcedencia = %s,
                    observaciones = %s,
                    idGeneracion = %s,
                    idGrupo = %s,
                    equivalencia = %s,
                    numeroControl = %s,
                    statusAlumno = %s,
                    curp = %s,
                    id_nivel_ingreso = %s,
                    certificado_incompleto = %s,
                    fecha_entrega_certificado = %s,
                    trae_boleta = %s,
                    estado_pago_equivalencia = %s
                WHERE idAlumno = %s
            """
            values = (
                data.get("nombre"),
                data.get("apPaterno"),
                data.get("apMaterno"),
                data.get("fechaNacimiento") or None,
                data.get("celularAlumno"),
                data.get("correoAlumno"),
                data.get("escuelaProcedencia"),
                data.get("observaciones"),
                data.get("idGeneracion") or None,
                data.get("idGrupo") or None,
                data.get("equivalencia") or "NO",
                data.get("numeroControl"),
                data.get("statusAlumno") or "ACTIVO",
                data.get("curp"),
                data.get("id_nivel_ingreso") or data.get("id_nivel_academico") or data.get("idNivelAcademico") or None,
                data.get("certificado_incompleto") or "NO",
                data.get("fecha_entrega_certificado") or None,
                data.get("trae_boleta") or "SI",
                data.get("estado_pago_equivalencia") or "PENDIENTE",
                id_alumno,
            )
            cursor.execute(query, values)

            # 1.1 Actualizar modalidad de estudio y dia_pago si se especifican
            if "modalidad_estudio" in data or "dia_pago" in data:
                mod_est = data.get("modalidad_estudio") or "PRESENCIAL"
                dia_p = data.get("dia_pago") or "SABADO"
                cursor.execute(
                    "UPDATE tb_alumnos SET modalidad_estudio = %s, dia_pago = %s WHERE idAlumno = %s",
                    (mod_est, dia_p, id_alumno)
                )

            # 2. Actualizar / Insertar dirección en tb_direcciones_alumno
            calle = data.get("calle")
            colonia = data.get("colonia")
            localidad = data.get("localidad")
            municipio = data.get("municipio")
            if any([calle, colonia, localidad, municipio]):
                cursor.execute("SELECT idDireccion FROM tb_direcciones_alumno WHERE idAlumno = %s", (id_alumno,))
                dir_row = cursor.fetchone()
                if dir_row:
                    cursor.execute("""
                        UPDATE tb_direcciones_alumno
                        SET calle = %s, colonia = %s, localidad = %s, municipio = %s
                        WHERE idAlumno = %s
                    """, (calle, colonia, localidad, municipio, id_alumno))
                else:
                    cursor.execute("""
                        INSERT INTO tb_direcciones_alumno (idAlumno, calle, colonia, localidad, municipio)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (id_alumno, calle, colonia, localidad, municipio))

            # 3. Actualizar / Insertar certificado en tb_certificados_alumno
            folio_cert = data.get("folioCertificado")
            recogio_cert = 1 if str(data.get("recogioCertificado", "")).upper() in ["SI", "1", "TRUE"] else 0
            fecha_recogio = data.get("fechaRecogioCertificado") or None
            if folio_cert or fecha_recogio or recogio_cert:
                cursor.execute("SELECT idCertificado FROM tb_certificados_alumno WHERE idAlumno = %s", (id_alumno,))
                cert_row = cursor.fetchone()
                if cert_row:
                    cursor.execute("""
                        UPDATE tb_certificados_alumno
                        SET folioCertificado = %s, recogioCertificado = %s, fechaRecogioCertificado = %s
                        WHERE idAlumno = %s
                    """, (folio_cert, recogio_cert, fecha_recogio, id_alumno))
                else:
                    cursor.execute("""
                        INSERT INTO tb_certificados_alumno (idAlumno, folioCertificado, recogioCertificado, fechaRecogioCertificado)
                        VALUES (%s, %s, %s, %s)
                    """, (id_alumno, folio_cert, recogio_cert, fecha_recogio))

            # 4. Actualizar / Insertar tutor en tb_contactos y tb_alumno_contacto
            tutor_nombre = data.get("tutor")
            parentesco = data.get("parentesco")
            tel_tutor = data.get("telefonoTutor")
            if tutor_nombre or parentesco or tel_tutor:
                cursor.execute("""
                    SELECT ac.id, ac.idContacto 
                    FROM tb_alumno_contacto ac 
                    WHERE ac.idAlumno = %s AND (ac.esTutor = 1 OR ac.esPrincipal = 1)
                """, (id_alumno,))
                cont_row = cursor.fetchone()
                if cont_row and cont_row.get("idContacto"):
                    cursor.execute("""
                        UPDATE tb_contactos 
                        SET nombre = %s, telefono = %s 
                        WHERE idContacto = %s
                    """, (tutor_nombre, tel_tutor, cont_row["idContacto"]))
                    cursor.execute("""
                        UPDATE tb_alumno_contacto 
                        SET parentesco = %s 
                        WHERE id = %s
                    """, (parentesco, cont_row["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_contactos (nombre, telefono) 
                        VALUES (%s, %s)
                    """, (tutor_nombre, tel_tutor))
                    nuevo_id_contacto = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO tb_alumno_contacto (idAlumno, idContacto, parentesco, esTutor, esPrincipal) 
                        VALUES (%s, %s, %s, 1, 1)
                    """, (id_alumno, nuevo_id_contacto, parentesco))

            # 5. Sincronizar tb_alumnoGrupo
            id_grupo = data.get("idGrupo") or data.get("id_Grupo")
            if id_grupo:
                cursor.execute("SELECT id FROM tb_alumnogrupo WHERE idAlumno = %s", (id_alumno,))
                relacion = cursor.fetchone()
                if relacion:
                    cursor.execute("""
                        UPDATE tb_alumnogrupo 
                        SET idGrupo = %s 
                        WHERE idAlumno = %s
                    """, (id_grupo, id_alumno))
                else:
                    cursor.execute("""
                        INSERT INTO tb_alumnogrupo (idAlumno, idGrupo) 
                        VALUES (%s, %s)
                    """, (id_alumno, id_grupo))
            else:
                cursor.execute("DELETE FROM tb_alumnogrupo WHERE idAlumno = %s", (id_alumno,))

            conexion.commit()
            return {"mensaje": "Alumno actualizado correctamente", "idAlumno": id_alumno}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    # OBTENER ALUMNOS POR GRUPO
    @staticmethod
    def get_alumnos_grupo(idGrupo):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.fechaNacimiento,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    a.modalidad_estudio,
                    a.dia_pago,
                    a.moodle_user_id,
                    a.moodle_username,
                    a.moodle_password,
                    a.semana_actual_pagada,
                    a.fecha_proximo_pago,
                    g.generacion AS nombreGeneracionTexto,
                    gr.clave AS nombreGrupoTexto,
                    d.calle,
                    d.colonia,
                    d.localidad,
                    d.municipio,
                    d.numeroExterior,
                    d.numeroInterior,
                    cert.folioCertificado,
                    cert.recogioCertificado,
                    cert.fechaRecogioCertificado,
                    CONCAT_WS(' ', c.nombre, c.apPaterno, c.apMaterno) AS tutor,
                    ac.parentesco,
                    COALESCE(c.telefono, c.celular) AS telefonoTutor
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_direcciones_alumno d ON a.idAlumno = d.idAlumno
                LEFT JOIN tb_certificados_alumno cert ON a.idAlumno = cert.idAlumno
                LEFT JOIN tb_alumno_contacto ac ON ac.id = (
                    SELECT MIN(ac2.id) FROM tb_alumno_contacto ac2 
                    WHERE ac2.idAlumno = a.idAlumno AND (ac2.esTutor = 1 OR ac2.esPrincipal = 1)
                )
                LEFT JOIN tb_contactos c ON ac.idContacto = c.idContacto
                WHERE a.idGrupo = %s
                ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
            """
            cursor.execute(query, (idGrupo,))
            alumnos = cursor.fetchall()
            return {"data": alumnos}
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_alumno_equivalencia(page=1, limit=50, search=""):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            if page < 1:
                page = 1
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200

            offset = (page - 1) * limit
            where = ["UPPER(a.equivalencia) = 'SI'"]
            valores = []

            if search:
                palabras = search.strip().split()
                for palabra in palabras:
                    where.append(
                        "(a.nombre LIKE %s OR a.apPaterno LIKE %s OR a.apMaterno LIKE %s)"
                    )
                    like = f"%{palabra}%"
                    valores.extend([like, like, like])

            where_sql = "WHERE " + " AND ".join(where)

            # Total de registros
            sql_total = f"SELECT COUNT(*) AS total FROM tb_alumnos a {where_sql}"
            cursor.execute(sql_total, valores)
            total = cursor.fetchone()["total"]

            # Consulta paginada
            sql_datos = f"""
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.fechaNacimiento,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    a.modalidad_estudio,
                    a.dia_pago,
                    a.moodle_user_id,
                    a.moodle_username,
                    a.moodle_password,
                    a.semana_actual_pagada,
                    a.fecha_proximo_pago,
                    g.generacion AS nombreGeneracionTexto,
                    d.calle,
                    d.colonia,
                    d.localidad,
                    d.municipio
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_direcciones_alumno d ON a.idAlumno = d.idAlumno
                {where_sql}
                ORDER BY a.idAlumno ASC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql_datos, valores + [limit, offset])
            data = cursor.fetchall()

            return {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
                "search": search,
                "data": data,
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_alumno_grupo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_alumnogrupo (idAlumno, idGrupo) VALUES (%s, %s)"
            cursor.execute(
                query,
                (
                    data.get("idAlumno"),
                    data.get("idGrupo"),
                ),
            )
            conexion.commit()
            return {"mensaje": "Alumno asignado al grupo correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _calcular_proxima_fecha_pago(dia_pago_nombre, semanas_adelante=1):
        """Calcula la fecha del próximo día de cobro (SABADO o DOMINGO)"""
        import datetime
        dias_map = {
            'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2, 'JUEVES': 3,
            'VIERNES': 4, 'SABADO': 5, 'DOMINGO': 6
        }
        target_day = dias_map.get(str(dia_pago_nombre).upper(), 5) # Default SABADO
        hoy = datetime.date.today()
        dias_faltantes = (target_day - hoy.weekday()) % 7
        if dias_faltantes == 0 and semanas_adelante > 0:
            dias_faltantes = 7
        fecha_proxima = hoy + datetime.timedelta(days=dias_faltantes)
        return fecha_proxima

    @staticmethod
    def cambiar_modalidad_online(id_alumno, data):
        from app.services.moodle_service import MoodleService
        import datetime
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT * FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))
            alumno = cursor.fetchone()
            if not alumno:
                return {"success": False, "error": "Alumno no encontrado"}, 404

            # REGLA ESTRICTA: El alumno debe estar ligado sí o sí a un grupo
            id_grupo = data.get("idGrupo") or alumno.get("idGrupo")
            if not id_grupo or int(id_grupo) <= 0:
                return {
                    "success": False,
                    "error": "El alumno debe estar asignado sí o sí a un grupo antes de cambiar a modalidad en línea."
                }, 400

            dia_pago = str(data.get("dia_pago", "SABADO")).upper()
            if dia_pago not in ['LUNES','MARTES','MIERCOLES','JUEVES','VIERNES','SABADO','DOMINGO']:
                dia_pago = 'SABADO'

            num_ctrl = alumno.get("numeroControl") or alumno.get("curp") or f"alu{id_alumno}"
            username = str(data.get("moodle_username") or num_ctrl).lower().strip()
            password = str(data.get("moodle_password") or f"Bti.{username}*")

            cursor.execute("SELECT id_curso_moodle, clave FROM tb_grupos WHERE id = %s", (id_grupo,))
            grupo_info = cursor.fetchone() or {}
            course_id = data.get("id_curso_moodle") or grupo_info.get("id_curso_moodle") or 50

            moodle_res = MoodleService.crear_usuario(
                username=username,
                password=password,
                firstname=alumno.get("nombre"),
                lastname=f"{alumno.get('apPaterno', '')} {alumno.get('apMaterno', '')}".strip(),
                email=alumno.get("correoAlumno")
            )
            moodle_user_id = moodle_res.get("moodle_user_id")

            if moodle_user_id and course_id:
                MoodleService.matricular_en_curso(moodle_user_id, course_id)

            fecha_prox = AlumnosService._calcular_proxima_fecha_pago(dia_pago, semanas_adelante=1)

            query = """
                UPDATE tb_alumnos SET
                    modalidad_estudio = 'ONLINE',
                    dia_pago = %s,
                    idGrupo = %s,
                    moodle_user_id = %s,
                    moodle_username = %s,
                    moodle_password = %s,
                    fecha_proximo_pago = %s
                WHERE idAlumno = %s
            """
            cursor.execute(query, (
                dia_pago,
                id_grupo,
                moodle_user_id,
                username,
                password,
                fecha_prox,
                id_alumno
            ))
            conexion.commit()

            return {
                "success": True,
                "mensaje": "Alumno asignado a modalidad en línea exitosamente.",
                "alumno": {
                    "idAlumno": id_alumno,
                    "modalidad_estudio": "ONLINE",
                    "dia_pago": dia_pago,
                    "idGrupo": id_grupo,
                    "fecha_proximo_pago": str(fecha_prox),
                    "moodle_user_id": moodle_user_id,
                    "moodle_username": username,
                    "moodle_password": password
                }
            }, 200
        except Exception as e:
            conexion.rollback()
            return {"success": False, "error": str(e)}, 500
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def cambiar_modalidad_presencial(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("UPDATE tb_alumnos SET modalidad_estudio = 'PRESENCIAL' WHERE idAlumno = %s", (id_alumno,))
            conexion.commit()
            return {"success": True, "mensaje": "Alumno retornado a modalidad presencial exitosamente."}, 200
        except Exception as e:
            conexion.rollback()
            return {"success": False, "error": str(e)}, 500
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def registrar_pago_online(id_alumno, data):
        from app.services.moodle_service import MoodleService
        import datetime
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT a.*, gr.id_curso_moodle, gr.clave AS nombreGrupo 
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                WHERE a.idAlumno = %s
            """, (id_alumno,))
            alumno = cursor.fetchone()
            if not alumno:
                return {"success": False, "error": "Alumno no encontrado"}, 404

            folio_ticket = str(data.get("folio_ticket", "")).strip()
            if not folio_ticket:
                return {"success": False, "error": "El folio del ticket es obligatorio."}, 400

            fecha_pago = data.get("fecha_pago")
            if not fecha_pago:
                fecha_pago = str(datetime.date.today())

            try:
                semana_cubierta = int(data.get("semana_cubierta", 1))
                if semana_cubierta < 1 or semana_cubierta > 4:
                    return {"success": False, "error": "La semana cubierta debe ser entre 1 y 4."}, 400
            except ValueError:
                return {"success": False, "error": "Semana cubierta inválida."}, 400

            monto = float(data.get("monto", 0.0) or 0.0)
            metodo_pago = str(data.get("metodo_pago", "EFECTIVO")).upper()
            observaciones = data.get("observaciones", "")
            registrado_por = data.get("registrado_por", "SISTEMA")

            sql_pago = """
                INSERT INTO tb_alumno_pagos 
                (id_alumno, fecha_pago, folio_ticket, semana_cubierta, monto, metodo_pago, observaciones, registrado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_pago, (
                id_alumno, fecha_pago, folio_ticket, semana_cubierta, monto, metodo_pago, observaciones, registrado_por
            ))
            id_pago = cursor.lastrowid

            moodle_user_id = alumno.get("moodle_user_id")
            course_id = alumno.get("id_curso_moodle") or 50
            sincronizado_moodle = 0

            if moodle_user_id and course_id:
                moodle_res = MoodleService.desbloquear_semana(moodle_user_id, course_id, semana_cubierta)
                if moodle_res.get("success"):
                    sincronizado_moodle = 1
                    cursor.execute("""
                        UPDATE tb_alumno_pagos 
                        SET sincronizado_moodle = 1, fecha_sincronizacion_moodle = NOW() 
                        WHERE id = %s
                    """, (id_pago,))

            nueva_semana = max(int(alumno.get("semana_actual_pagada") or 0), semana_cubierta)
            dia_pago = alumno.get("dia_pago") or "SABADO"
            nueva_fecha_prox = AlumnosService._calcular_proxima_fecha_pago(dia_pago, semanas_adelante=1)

            cursor.execute("""
                UPDATE tb_alumnos SET
                    semana_actual_pagada = %s,
                    fecha_proximo_pago = %s
                WHERE idAlumno = %s
            """, (nueva_semana, nueva_fecha_prox, id_alumno))

            conexion.commit()

            return {
                "success": True,
                "mensaje": f"Pago registrado exitosamente con ticket {folio_ticket}. Semana {semana_cubierta} habilitada en Moodle.",
                "pago": {
                    "id": id_pago,
                    "folio_ticket": folio_ticket,
                    "semana_cubierta": semana_cubierta,
                    "fecha_pago": str(fecha_pago),
                    "monto": monto,
                    "sincronizado_moodle": bool(sincronizado_moodle),
                    "nueva_semana_pagada": nueva_semana,
                    "fecha_proximo_pago": str(nueva_fecha_prox)
                }
            }, 200
        except Exception as e:
            conexion.rollback()
            return {"success": False, "error": str(e)}, 500
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_pagos_alumno(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT 
                    id, id_alumno, fecha_pago, folio_ticket, semana_cubierta,
                    monto, metodo_pago, observaciones, registrado_por,
                    sincronizado_moodle, fecha_sincronizacion_moodle, created_at
                FROM tb_alumno_pagos
                WHERE id_alumno = %s
                ORDER BY semana_cubierta DESC, fecha_pago DESC, id DESC
            """, (id_alumno,))
            pagos = cursor.fetchall()
            return {"success": True, "data": pagos}, 200
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_widget_data(moodle_user_id=None, id_alumno=None):
        import datetime
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            where_clause = ""
            param = None
            if moodle_user_id:
                where_clause = "a.moodle_user_id = %s"
                param = moodle_user_id
            elif id_alumno:
                where_clause = "a.idAlumno = %s"
                param = id_alumno
            else:
                return {"es_online": False, "mensaje": "Falta parámetro moodle_user_id o id_alumno"}, 400

            cursor.execute(f"""
                SELECT 
                    a.idAlumno, a.nombre, a.apPaterno, a.apMaterno,
                    a.modalidad_estudio, a.dia_pago, a.moodle_user_id,
                    a.semana_actual_pagada, a.fecha_proximo_pago,
                    gr.clave AS nombreGrupo,
                    m.nombreMateria
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_materias m ON m.id = (
                    SELECT MIN(pem.idMateria) FROM plan_estudio_materia pem WHERE pem.idPlanEstudio = gr.id_planEstudios
                )
                WHERE {where_clause}
            """, (param,))
            alumno = cursor.fetchone()

            if not alumno or alumno.get("modalidad_estudio") != "ONLINE":
                return {"es_online": False}, 200

            hoy = datetime.date.today()
            prox_pago = alumno.get("fecha_proximo_pago")
            semana = int(alumno.get("semana_actual_pagada") or 0)
            
            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            fecha_str = "Pronto"
            al_corriente = True

            if prox_pago:
                if isinstance(prox_pago, str):
                    prox_pago = datetime.datetime.strptime(prox_pago, "%Y-%m-%d").date()
                dia_semana_nombre = alumno.get("dia_pago", "SABADO").capitalize()
                fecha_str = f"{dia_semana_nombre} {prox_pago.day} de {meses[prox_pago.month]}"
                if hoy > prox_pago:
                    al_corriente = False

            return {
                "es_online": True,
                "id_alumno": alumno["idAlumno"],
                "nombre_completo": f"{alumno['nombre']} {alumno['apPaterno']}".strip(),
                "estado_pago": "Al corriente" if al_corriente else "Pago pendiente",
                "estado_color": "#16a34a" if al_corriente else "#dc2626",
                "semana_actual": semana,
                "total_semanas": 4,
                "porcentaje_progreso": int((semana / 4.0) * 100),
                "fecha_proximo_pago": fecha_str,
                "dia_pago": alumno.get("dia_pago", "SABADO"),
                "materia_en_curso": alumno.get("nombreMateria") or "Materia Online Asignada",
                "grupo": alumno.get("nombreGrupo")
            }, 200
        finally:
            cursor.close()
            conexion.close()
