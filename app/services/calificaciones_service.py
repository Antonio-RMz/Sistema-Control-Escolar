from app.config.conexion import get_connection

class CalificacionesService:

    @staticmethod
    def get_kardex_alumno(id_alumno):
        """
        Obtiene el Kárdex completo del alumno organizado por Periodos/Niveles Académicos,
        calculando los promedios por periodo y el promedio global.
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Obtener datos generales del alumno y su CCT
            cursor.execute("""
                SELECT 
                    a.idAlumno,
                    a.nombre,
                    a.apPaterno,
                    a.apMaterno,
                    a.numeroControl,
                    a.statusAlumno,
                    a.curp,
                    a.idGeneracion,
                    a.idGrupo,
                    a.equivalencia,
                    a.id_nivel_ingreso,
                    nei.numero AS numeroNivelIngreso,
                    COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3) AS id_centroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    ct.clave AS claveCentroTrabajo,
                    g.nombreGeneracion,
                    gr.clave AS claveGrupo
                FROM tb_alumnos a
                LEFT JOIN tb_generaciones g ON a.idGeneracion = g.id
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON ct.id = COALESCE(gr.id_centroTrabajo, g.id_centroTrabajo, 3)
                LEFT JOIN tb_niveles_academicos nei ON a.id_nivel_ingreso = nei.id
                WHERE a.idAlumno = %s
            """, (id_alumno,))
            alumno = cursor.fetchone()
            if not alumno:
                return {"error": "Alumno no encontrado"}

            id_cct = alumno["id_centroTrabajo"]

            # 2. Obtener los niveles académicos correspondientes a este CCT (ej. 1º a 6º Trimestre o Semestre)
            cursor.execute("""
                SELECT 
                    n.id AS idNivel,
                    n.nombre AS nombreNivel,
                    n.numero AS numeroNivel,
                    n.tipo AS tipoPeriodo
                FROM tb_niveles_academicos n
                JOIN tb_tipoperiodo tp ON n.id_tipoPeriodo = tp.id
                JOIN tb_centrotrabajo ct ON ct.idTipoPeriodo = tp.id
                WHERE ct.id = %s AND n.activo = 1
                ORDER BY n.numero ASC
            """, (id_cct,))
            niveles = cursor.fetchall()
            if not niveles:
                # Fallback: consultar todos los niveles del tipo de periodo de BGNE o BTI
                cursor.execute("SELECT id AS idNivel, nombre AS nombreNivel, numero AS numeroNivel, tipo AS tipoPeriodo FROM tb_niveles_academicos ORDER BY id_tipoPeriodo ASC, numero ASC")
                niveles = cursor.fetchall()

            # 3. Obtener todas las materias del CCT y las calificaciones registradas para este alumno
            cursor.execute("""
                SELECT 
                    m.id AS idMateria,
                    m.nombreMateria,
                    m.clave AS claveMateria,
                    m.id_nivel_academico,
                    c.id AS idCalificacion,
                    c.calificacion,
                    c.tipoAcreditacion,
                    c.observaciones,
                    c.fechaEvaluacion,
                    c.idGrupo,
                    c.parcial1,
                    c.parcial2,
                    c.parcial3,
                    c.semestral,
                    c.extraordinario,
                    c.asistencias,
                    c.total_asistencias
                FROM tb_materias m
                LEFT JOIN tb_calificaciones c ON c.idMateria = m.id AND c.idAlumno = %s
                WHERE (m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL)
                ORDER BY m.id_nivel_academico ASC, COALESCE(m.orden, m.id) ASC
            """, (id_alumno, id_cct))
            materias_califs = cursor.fetchall()

            # 4. Agrupar materias y calificaciones por Nivel Académico
            kardex_periodos = []
            suma_calif_global = 0.0
            total_materias_evaluadas = 0

            for nivel in niveles:
                id_nivel = nivel["idNivel"]
                mats_nivel = [m for m in materias_califs if m.get("id_nivel_academico") == id_nivel]
                
                suma_periodo = 0.0
                evaluadas_periodo = 0

                lista_materias_periodo = []
                for mat in mats_nivel:
                    calif_val = mat.get("calificacion")
                    tiene_calif = calif_val is not None
                    
                    is_equiv = False
                    if alumno.get("equivalencia") == "SI" and alumno.get("numeroNivelIngreso") is not None:
                        if int(alumno["numeroNivelIngreso"]) > int(nivel["numeroNivel"]):
                            is_equiv = True
                    
                    if tiene_calif:
                        c_num = float(calif_val)
                        suma_periodo += c_num
                        evaluadas_periodo += 1
                        suma_calif_global += c_num
                        total_materias_evaluadas += 1

                    lista_materias_periodo.append({
                        "idMateria": mat["idMateria"],
                        "nombreMateria": mat["nombreMateria"],
                        "claveMateria": mat["claveMateria"],
                        "idCalificacion": mat["idCalificacion"],
                        "calificacion": float(calif_val) if tiene_calif else None,
                        "es_equivalencia": is_equiv,
                        "tipoAcreditacion": mat.get("tipoAcreditacion") or ("EQUIVALENCIA" if is_equiv else "ORDINARIO"),
                        "observaciones": mat.get("observaciones"),
                        "fechaEvaluacion": str(mat["fechaEvaluacion"]) if mat.get("fechaEvaluacion") else None,
                        "aprobada": float(calif_val) >= 6.0 if tiene_calif else False,
                        "parcial1": float(mat["parcial1"]) if mat.get("parcial1") is not None else None,
                        "parcial2": float(mat["parcial2"]) if mat.get("parcial2") is not None else None,
                        "parcial3": float(mat["parcial3"]) if mat.get("parcial3") is not None else None,
                        "semestral": float(mat["semestral"]) if mat.get("semestral") is not None else None,
                        "extraordinario": float(mat["extraordinario"]) if mat.get("extraordinario") is not None else None,
                        "asistencias": int(mat["asistencias"]) if mat.get("asistencias") is not None else None,
                        "total_asistencias": int(mat["total_asistencias"]) if mat.get("total_asistencias") is not None else None,
                    })

                promedio_periodo = round(suma_periodo / evaluadas_periodo, 1) if evaluadas_periodo > 0 else None

                kardex_periodos.append({
                    "idNivel": id_nivel,
                    "nombrePeriodo": nivel["nombreNivel"],
                    "numeroPeriodo": nivel["numeroNivel"],
                    "tipoPeriodo": nivel["tipoPeriodo"],
                    "materias": lista_materias_periodo,
                    "promedio": promedio_periodo,
                    "totalMaterias": len(lista_materias_periodo),
                    "totalAcreditadas": sum(1 for m in lista_materias_periodo if m["aprobada"])
                })

            promedio_general = round(suma_calif_global / total_materias_evaluadas, 1) if total_materias_evaluadas > 0 else None

            return {
                "alumno": alumno,
                "periodos": kardex_periodos,
                "promedioGeneral": promedio_general,
                "totalMateriasEvaluadas": total_materias_evaluadas
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_calificaciones_alumno(id_alumno, calificaciones, create_by="SISTEMA"):
        """
        Guarda o actualiza una lista de calificaciones para un alumno.
        calificaciones: [ { "idMateria": 8, "id_nivel_academico": 1, "calificacion": 8.5, "tipoAcreditacion": "ORDINARIO", "observaciones": "..." } ]
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            for item in calificaciones:
                id_materia = item.get("idMateria")
                calificacion = item.get("calificacion")
                id_nivel = item.get("id_nivel_academico")
                tipo_acred = item.get("tipoAcreditacion") or "ORDINARIO"
                observaciones = item.get("observaciones")
                id_grupo = item.get("idGrupo") or None

                if not id_materia:
                    continue

                if calificacion is None:
                    # Si la calificación se envía vacía o se revierte a equivalencia, eliminar la calificación si existe
                    cursor.execute("""
                        DELETE FROM tb_calificaciones 
                        WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                    """, (id_alumno, id_materia, tipo_acred))
                    continue

                # Verificar si ya existe calificación para este alumno, materia y tipo de acreditación
                cursor.execute("""
                    SELECT id FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                """, (id_alumno, id_materia, tipo_acred))
                existente = cursor.fetchone()

                parcial1 = item.get("parcial1")
                parcial2 = item.get("parcial2")
                parcial3 = item.get("parcial3")
                semestral = item.get("semestral")
                extraordinario = item.get("extraordinario")
                asistencias = item.get("asistencias")
                total_asistencias = item.get("total_asistencias")

                p1_val = float(parcial1) if (parcial1 is not None and parcial1 != "") else None
                p2_val = float(parcial2) if (parcial2 is not None and parcial2 != "") else None
                p3_val = float(parcial3) if (parcial3 is not None and parcial3 != "") else None
                sem_val = float(semestral) if (semestral is not None and semestral != "") else None
                ext_val = float(extraordinario) if (extraordinario is not None and extraordinario != "") else None
                asist_val = int(asistencias) if (asistencias is not None and asistencias != "") else None
                tot_asist_val = int(total_asistencias) if (total_asistencias is not None and total_asistencias != "") else None

                if existente:
                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, id_nivel_academico = %s, idGrupo = %s, observaciones = %s,
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s, 
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calificacion, id_nivel, id_grupo, observaciones, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val, create_by, existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones (
                            idAlumno, idMateria, id_nivel_academico, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy,
                            parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_alumno, id_materia, id_nivel, id_grupo, calificacion, tipo_acred, observaciones, create_by, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val))

            conexion.commit()
            return {"success": True, "message": "Calificaciones guardadas exitosamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_calificaciones_grupo_materia(id_grupo, id_materia=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            # 1. Información del grupo
            cursor.execute("""
                SELECT 
                    g.id,
                    g.clave,
                    g.fechaInicio,
                    g.fechaFin,
                    g.id_centroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    ct.clave AS claveCentroTrabajo,
                    g.id_nivel_academico,
                    na.nombre AS nombreNivel,
                    g.modalidadHorario,
                    tp.nombrePeriodo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                LEFT JOIN tb_niveles_academicos na ON g.id_nivel_academico = na.id
                LEFT JOIN tb_tipoperiodo tp ON g.id_tipoPeriodo = tp.id
                WHERE g.id = %s
            """, (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                return {"error": "Grupo no encontrado"}

            # 2. Obtener materias y docentes asociados a este grupo (de tb_horarios o del CCT)
            cursor.execute("""
                SELECT DISTINCT 
                    m.id AS idMateria,
                    m.nombreMateria,
                    m.clave AS claveMateria,
                    m.id_nivel_academico,
                    na.nombre AS nombreNivel,
                    na.numero AS numeroNivel,
                    h.id_docente,
                    CONCAT(d.nombreDocente, ' ', IFNULL(d.apPaternoDocente, ''), ' ', IFNULL(d.apMaternoDocente, '')) AS nombreDocente,
                    d.nivelEstudios,
                    COALESCE(m.orden, m.id) AS ordenMateria
                FROM tb_horarios h
                JOIN tb_materias m ON h.id_materia = m.id
                LEFT JOIN tb_niveles_academicos na ON m.id_nivel_academico = na.id
                LEFT JOIN tb_docentes d ON h.id_docente = d.idDocente
                WHERE h.id_grupo = %s
                ORDER BY ordenMateria ASC
            """, (id_grupo,))
            materias_horario = cursor.fetchall()

            # Si no hay materias en tb_horarios para este grupo, traer las materias de su CCT/Nivel
            if not materias_horario:
                cursor.execute("""
                    SELECT 
                        m.id AS idMateria,
                        m.nombreMateria,
                        m.clave AS claveMateria,
                        m.id_nivel_academico,
                        na.nombre AS nombreNivel,
                        na.numero AS numeroNivel,
                        NULL AS id_docente,
                        'Sin docente asignado' AS nombreDocente,
                        NULL AS nivelEstudios,
                        COALESCE(m.orden, m.id) AS ordenMateria
                    FROM tb_materias m
                    LEFT JOIN tb_niveles_academicos na ON m.id_nivel_academico = na.id
                    WHERE m.idCentroTrabajo = %s OR m.idCentroTrabajo IS NULL
                    ORDER BY m.id_nivel_academico ASC, ordenMateria ASC
                """, (grupo.get("id_centroTrabajo") or grupo.get("id_centro_trabajo") or 3,))
                materias_horario = cursor.fetchall()

            if not id_materia and materias_horario:
                id_materia = materias_horario[0]["idMateria"]

            # Docente de la materia seleccionada
            materia_seleccionada = None
            for m in materias_horario:
                if str(m["idMateria"]) == str(id_materia):
                    materia_seleccionada = m
                    break

            # 3. Lista de alumnos del grupo con sus calificaciones en esta materia
            alumnos_califs = []
            if id_materia:
                # Obtener el número de nivel de la materia actual
                numero_nivel_materia = 1
                if materia_seleccionada and materia_seleccionada.get("numeroNivel") is not None:
                    numero_nivel_materia = int(materia_seleccionada["numeroNivel"])
                else:
                    cursor.execute("SELECT numero FROM tb_niveles_academicos WHERE id = (SELECT id_nivel_academico FROM tb_materias WHERE id = %s)", (id_materia,))
                    nivel_row = cursor.fetchone()
                    if nivel_row and nivel_row.get("numero") is not None:
                        numero_nivel_materia = int(nivel_row["numero"])

                cursor.execute("""
                    SELECT 
                        a.idAlumno,
                        a.numeroControl AS matricula,
                        a.nombre,
                        a.apPaterno,
                        a.apMaterno,
                        a.curp,
                        a.statusAlumno,
                        a.equivalencia,
                        a.id_nivel_ingreso,
                        nei.numero AS numeroNivelIngreso,
                        c.id AS idCalificacion,
                        c.calificacion,
                        c.tipoAcreditacion,
                        c.observaciones,
                        c.parcial1,
                        c.parcial2,
                        c.parcial3,
                        c.semestral,
                        c.extraordinario,
                        c.asistencias,
                        c.total_asistencias
                    FROM tb_alumnos a
                    LEFT JOIN tb_niveles_academicos nei ON a.id_nivel_ingreso = nei.id
                    LEFT JOIN tb_calificaciones c ON c.idAlumno = a.idAlumno AND c.idMateria = %s
                    WHERE a.idGrupo = %s
                    ORDER BY a.apPaterno ASC, a.apMaterno ASC, a.nombre ASC
                """, (id_materia, id_grupo))
                alumnos_califs = cursor.fetchall()

                # Determinar si cada alumno tiene estatus de equivalencia para este periodo
                for a in alumnos_califs:
                    is_equiv = False
                    if a.get("equivalencia") == "SI" and a.get("numeroNivelIngreso") is not None:
                        if int(a["numeroNivelIngreso"]) > numero_nivel_materia:
                            is_equiv = True
                    a["es_equivalencia"] = is_equiv

            return {
                "grupo": grupo,
                "materias": materias_horario,
                "materiaSeleccionada": materia_seleccionada,
                "idMateriaSeleccionada": int(id_materia) if id_materia else None,
                "alumnos": alumnos_califs
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def guardar_calificaciones_grupo_materia(id_grupo, id_materia, calificaciones, create_by="SISTEMA"):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            for item in calificaciones:
                id_alumno = item.get("idAlumno")
                calificacion = item.get("calificacion")
                observaciones = item.get("observaciones") or ""
                tipo_acred = item.get("tipoAcreditacion") or "ORDINARIO"

                if not id_alumno or calificacion is None or calificacion == "":
                    continue

                calif_val = float(calificacion)
                
                parcial1 = item.get("parcial1")
                parcial2 = item.get("parcial2")
                parcial3 = item.get("parcial3")
                semestral = item.get("semestral")
                extraordinario = item.get("extraordinario")
                asistencias = item.get("asistencias")
                total_asistencias = item.get("total_asistencias")

                p1_val = float(parcial1) if (parcial1 is not None and parcial1 != "") else None
                p2_val = float(parcial2) if (parcial2 is not None and parcial2 != "") else None
                p3_val = float(parcial3) if (parcial3 is not None and parcial3 != "") else None
                sem_val = float(semestral) if (semestral is not None and semestral != "") else None
                ext_val = float(extraordinario) if (extraordinario is not None and extraordinario != "") else None
                asist_val = int(asistencias) if (asistencias is not None and asistencias != "") else None
                tot_asist_val = int(total_asistencias) if (total_asistencias is not None and total_asistencias != "") else None

                cursor.execute("""
                    SELECT id FROM tb_calificaciones 
                    WHERE idAlumno = %s AND idMateria = %s AND tipoAcreditacion = %s
                """, (id_alumno, id_materia, tipo_acred))
                existente = cursor.fetchone()

                if existente:
                    cursor.execute("""
                        UPDATE tb_calificaciones 
                        SET calificacion = %s, idGrupo = %s, observaciones = %s, 
                            parcial1 = %s, parcial2 = %s, parcial3 = %s, semestral = %s, extraordinario = %s, 
                            asistencias = %s, total_asistencias = %s,
                            updateBy = %s, updateAt = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (calif_val, id_grupo, observaciones, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val, create_by, existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO tb_calificaciones (
                            idAlumno, idMateria, idGrupo, calificacion, tipoAcreditacion, observaciones, fechaEvaluacion, createBy,
                            parcial1, parcial2, parcial3, semestral, extraordinario, asistencias, total_asistencias
                        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_alumno, id_materia, id_grupo, calif_val, tipo_acred, observaciones, create_by, p1_val, p2_val, p3_val, sem_val, ext_val, asist_val, tot_asist_val))

            conexion.commit()
            return {"success": True, "message": "Calificaciones del grupo guardadas correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
