from app.config.conexion import get_connection
import pandas as pd
import math


class AlumnosService:
    @staticmethod
    def get_alumnos(page=1, limit=50, generacion=None, idGrupo=None, search="", id_centro_trabajo=None, status_alumno=None, order="ASC"):
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
            ap_paterno = (alumno_data.get("apPaterno") or "").strip()
            ap_materno = (alumno_data.get("apMaterno") or "").strip()
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

            # Validación requeridos básicos de alumno
            if not nombre or not ap_paterno:
                return {"error": "El nombre y apellido paterno del alumno son obligatorios."}, 400

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
                
                if cct_tipo_periodo and nivel_row.get("id_tipoPeriodo") and int(nivel_row.get("id_tipoPeriodo")) != int(cct_tipo_periodo):
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

                if id_nivel_academico and grupo_row.get("id_nivel_academico") and int(grupo_row["id_nivel_academico"]) != int(id_nivel_academico):
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
                    INSERT INTO tb_cursoExtraAlumno (
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
            # Eliminar cursos extracurriculares del alumno
            cursor.execute(
                "DELETE FROM tb_cursoExtraAlumno WHERE idAlumno = %s", (id_alumno,)
            )

            # Eliminar relación alumno-grupo
            cursor.execute(
                "DELETE FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,)
            )

            # Eliminar alumno
            cursor.execute("DELETE FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))

            conexion.commit()

            return {"mensaje": "Alumno eliminado correctamente", "idAlumno": id_alumno}

        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}

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
                cursor.execute("SELECT id FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))
                relacion = cursor.fetchone()
                if relacion:
                    cursor.execute("""
                        UPDATE tb_alumnoGrupo 
                        SET idGrupo = %s 
                        WHERE idAlumno = %s
                    """, (id_grupo, id_alumno))
                else:
                    cursor.execute("""
                        INSERT INTO tb_alumnoGrupo (idAlumno, idGrupo) 
                        VALUES (%s, %s)
                    """, (id_alumno, id_grupo))
            else:
                cursor.execute("DELETE FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))

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
            query = "INSERT INTO tb_alumnoGrupo (idAlumno, idGrupo) VALUES (%s, %s)"
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