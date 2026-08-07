from app.config.conexion import get_connection
import pandas as pd
import math


class AlumnosService:
    @staticmethod
    def get_alumnos(page=1, limit=50, generacion=None, idGrupo=None, search=""):
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

            # Consulta paginada
            sql_datos = f"""
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.fechaNacimiento,
                    a.tutor,
                    a.parentesco,
                    a.calle,
                    a.colonia,
                    a.localidad,
                    a.municipio,
                    a.telefonoTutor,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    g.generacion AS nombreGeneracionTexto,
                    gr.clave AS nombreGrupoTexto,
                    a.numeroControl,
                    a.statusAlumno,
                    a.folioCertificado,
                    a.curp,
                    a.fechaRecogioCertificado,
                    a.recogioCertificado
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                {where_sql}
                ORDER BY a.idAlumno ASC
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
##CREAR ALUMNOOOO
    @staticmethod
    def create_alumno(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO tb_alumnos (
                    nombre, apPaterno, apMaterno, fechaNacimiento, tutor, 
                    parentesco, calle, colonia, localidad, municipio, 
                    telefonoTutor, celularAlumno, correoAlumno, 
                    escuelaProcedencia, observaciones, idGeneracion, idGrupo,
                    equivalencia, numeroControl, statusAlumno, 
                    folioCertificado, curp, fechaRecogioCertificado, recogioCertificado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Extraer idGeneracion e idGrupo considerando ambas posibles nomenclaturas
            id_generacion = data.get("idGeneracion") or data.get("id_Generacion")
            id_grupo = data.get("idGrupo") or data.get("id_Grupo")

            values = (
                data.get("nombre"),
                data.get("apPaterno"),
                data.get("apMaterno"),
                data.get("fechaNacimiento"),
                data.get("tutor"),
                data.get("parentesco"),
                data.get("calle"),
                data.get("colonia"),
                data.get("localidad"),
                data.get("municipio"),
                data.get("telefonoTutor"),
                data.get("celularAlumno"),
                data.get("correoAlumno"),
                data.get("escuelaProcedencia"),
                data.get("observaciones"),
                id_generacion,
                id_grupo,
                data.get("equivalencia"),
                data.get("numeroControl"),
                data.get("statusAlumno"),
                data.get("folioCertificado"),
                data.get("curp"),
                data.get("fechaRecogioCertificado"),
                data.get("recogioCertificado")
            )
            cursor.execute(query, values)

            # Obtener el ID del alumno insertado
            id_alumno = cursor.lastrowid

            # Insertar la relación alumno-grupo si se proporcionó un idGrupo
            if id_grupo:
                query_grupo = (
                    "INSERT INTO tb_alumnoGrupo (idAlumno, idGrupo) VALUES (%s, %s)"
                )
                cursor.execute(query_grupo, (id_alumno, id_grupo))

            # Insertar los cursos extracurriculares si vienen en el arreglo
            cursos = data.get("cursos")
            if cursos and isinstance(cursos, list):
                query_cursos = """
                    INSERT INTO tb_cursoExtraAlumno (
                        idCursoExtracurricular, idAlumno, createDate, lastUpdateDate
                    ) VALUES (%s, %s, NOW(), NOW())
                """
                for id_curso in cursos:
                    cursor.execute(query_cursos, (id_curso, id_alumno))

            conexion.commit()
            return {"mensaje": "Alumno creado correctamente", "idAlumno": id_alumno}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
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
#PARA TRAERSE TODOS LOS ALUMNOS
    @staticmethod
    def get_alumno(id_alumno):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT * FROM tb_alumnos WHERE idAlumno = %s", (id_alumno,))
            alumno = cursor.fetchone()
            return {"data": alumno}
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
    #PARA ACTUALIZAR ALUMNOS 
    @staticmethod
    def update_alumno(id_alumno, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE tb_alumnos 
                SET
                    nombre = %s,
                    apPaterno = %s,
                    apMaterno = %s,
                    fechaNacimiento = %s,
                    tutor = %s,
                    parentesco = %s,
                    calle = %s,
                    colonia = %s,
                    localidad = %s,
                    municipio = %s,
                    telefonoTutor = %s,
                    celularAlumno = %s,
                    correoAlumno = %s,
                    escuelaProcedencia = %s,
                    observaciones = %s,
                    idGeneracion = %s,
                    idGrupo = %s,
                    equivalencia = %s,
                    numeroControl = %s,
                    statusAlumno = %s,
                    folioCertificado = %s,
                    curp = %s,
                    fechaRecogioCertificado = %s,
                    recogioCertificado = %s
                WHERE idAlumno = %s
            """
            values = (
                data.get("nombre"),
                data.get("apPaterno"),
                data.get("apMaterno"),
                data.get("fechaNacimiento"),
                data.get("tutor"),
                data.get("parentesco"),
                data.get("calle"),
                data.get("colonia"),
                data.get("localidad"),
                data.get("municipio"),
                data.get("telefonoTutor"),
                data.get("celularAlumno"),
                data.get("correoAlumno"),
                data.get("escuelaProcedencia"),
                data.get("observaciones"),
                data.get("idGeneracion"),
                data.get("idGrupo"),
                data.get("equivalencia"),
                data.get("numeroControl"),
                data.get("statusAlumno"),
                data.get("folioCertificado"),
                data.get("curp"),
                data.get("fechaRecogioCertificado"),
                data.get("recogioCertificado"),
                id_alumno,
            )
            cursor.execute(query, values)
            
            # Sincronizar tb_alumnoGrupo
            id_grupo = data.get("idGrupo") or data.get("id_Grupo")
            if id_grupo:
                # Verificar si ya existe una relación para este alumno
                cursor.execute("SELECT id FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))
                relacion = cursor.fetchone()
                if relacion:
                    # Si existe, actualizamos la relación
                    cursor.execute("""
                        UPDATE tb_alumnoGrupo 
                        SET idGrupo = %s 
                        WHERE idAlumno = %s
                    """, (id_grupo, id_alumno))
                else:
                    # Si no existe, creamos la relación
                    cursor.execute("""
                        INSERT INTO tb_alumnoGrupo (idAlumno, idGrupo) 
                        VALUES (%s, %s)
                    """, (id_alumno, id_grupo))
            else:
                # Si idGrupo es None o vacío, eliminamos cualquier relación existente
                cursor.execute("DELETE FROM tb_alumnoGrupo WHERE idAlumno = %s", (id_alumno,))

            conexion.commit()
            return {"mensaje": "Alumno actualizado correctamente", "idAlumno": id_alumno}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

            ##obtener alumnos por grupo
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
                    a.tutor,
                    a.parentesco,
                    a.calle,
                    a.colonia,
                    a.localidad,
                    a.municipio,
                    a.telefonoTutor,
                    a.celularAlumno,
                    a.correoAlumno,
                    a.escuelaProcedencia,
                    a.observaciones,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    g.generacion AS nombreGeneracionTexto,
                    gr.clave AS nombreGrupoTexto,
                    a.numeroControl,
                    a.statusAlumno,
                    a.folioCertificado,
                    a.curp,
                    a.fechaRecogioCertificado,
                    a.recogioCertificado
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                WHERE a.idGrupo = %s
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
                    a.idAlumno, a.nombre, a.apPaterno, a.apMaterno, a.fechaNacimiento,
                    a.tutor, a.parentesco, a.calle, a.colonia, a.localidad, a.municipio,
                    a.telefonoTutor, a.celularAlumno, a.correoAlumno,
                    a.escuelaProcedencia, a.observaciones, a.idGeneracion, a.idGrupo, a.equivalencia,
                    g.generacion AS nombreGeneracionTexto
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
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