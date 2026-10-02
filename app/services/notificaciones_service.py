import datetime
from app.config.conexion import get_connection


def get_mexico_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Mexico_City"))
    except Exception:
        return datetime.datetime.utcnow() - datetime.timedelta(hours=6)

class NotificacionesService:
    @staticmethod
    def _asegurar_tabla_alertas(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_alertas_ignoradas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                id_referencia INT NOT NULL,
                subtipo VARCHAR(50) NOT NULL DEFAULT 'general',
                accion VARCHAR(50) NOT NULL DEFAULT 'ignorar',
                motivo VARCHAR(255) NULL,
                nombre VARCHAR(255) NULL,
                cct VARCHAR(100) NULL,
                grupo VARCHAR(100) NULL,
                usuario VARCHAR(100) NULL,
                limpiado TINYINT(1) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_alerta (tipo, id_referencia, subtipo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            SELECT COUNT(*) AS total FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_alertas_ignoradas' AND COLUMN_NAME = 'limpiado';
        """)
        row_col = cursor.fetchone()
        col_exists = (row_col[0] if isinstance(row_col, (list, tuple)) else (row_col.get('total', 0) if isinstance(row_col, dict) else 0)) > 0
        if not col_exists:
            cursor.execute("ALTER TABLE tb_alertas_ignoradas ADD COLUMN limpiado TINYINT(1) DEFAULT 0;")

    @staticmethod
    def resolver_alerta(tipo, id_referencia, accion='resuelto', subtipo='general', motivo=None, usuario=None):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            NotificacionesService._asegurar_tabla_alertas(cursor)
            
            # Obtener datos de referencia para histórico
            nombre = None
            cct = None
            grupo = None
            if tipo in ('documentos', 'equivalencias', 'nuevos_alumnos'):
                cursor.execute("""
                    SELECT CONCAT_WS(' ', a.nombre, a.apPaterno, a.apMaterno) AS nombre,
                           gr.clave AS grupo, ct.nombre AS cct
                    FROM tb_alumnos a
                    LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                    LEFT JOIN tb_centrotrabajo ct ON COALESCE(gr.id_centroTrabajo, a.id_nivel_ingreso) = ct.id
                    WHERE a.idAlumno = %s
                """, (id_referencia,))
                row = cursor.fetchone()
                if row:
                    nombre = row["nombre"] if isinstance(row, dict) else row[0]
                    grupo = row["grupo"] if isinstance(row, dict) else row[1]
                    cct = row["cct"] if isinstance(row, dict) else row[2]
            elif tipo == 'grupos':
                cursor.execute("""
                    SELECT g.clave AS grupo, ct.nombre AS cct
                    FROM tb_grupos g
                    LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                    WHERE g.id = %s
                """, (id_referencia,))
                row = cursor.fetchone()
                if row:
                    grupo = row["grupo"] if isinstance(row, dict) else row[0]
                    nombre = f"Grupo {grupo}"
                    cct = row["cct"] if isinstance(row, dict) else row[1]

            # Registrar en tb_alertas_ignoradas (limpiado en 0)
            cursor.execute("""
                INSERT INTO tb_alertas_ignoradas 
                (tipo, id_referencia, subtipo, accion, motivo, nombre, cct, grupo, usuario, limpiado, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW())
                ON DUPLICATE KEY UPDATE 
                    accion = VALUES(accion),
                    motivo = VALUES(motivo),
                    nombre = VALUES(nombre),
                    cct = VALUES(cct),
                    grupo = VALUES(grupo),
                    usuario = VALUES(usuario),
                    limpiado = 0,
                    created_at = NOW()
            """, (tipo, id_referencia, subtipo, accion, motivo, nombre, cct, grupo, usuario))

            # Si es resuelto y tipo es documentos, actualizar la tabla tb_alumnos
            if accion == 'resuelto' and tipo == 'documentos':
                if subtipo == 'boleta':
                    cursor.execute("UPDATE tb_alumnos SET trae_boleta = 'SI' WHERE idAlumno = %s", (id_referencia,))
                elif subtipo == 'certificado':
                    cursor.execute("UPDATE tb_alumnos SET certificado_incompleto = 'NO' WHERE idAlumno = %s", (id_referencia,))
                else:
                    cursor.execute("UPDATE tb_alumnos SET trae_boleta = 'SI', certificado_incompleto = 'NO' WHERE idAlumno = %s", (id_referencia,))
            elif accion == 'resuelto' and tipo == 'equivalencias':
                cursor.execute("UPDATE tb_alumnos SET estado_pago_equivalencia = 'PAGADO' WHERE idAlumno = %s", (id_referencia,))

            conexion.commit()
            return {"success": True, "message": "Advertencia actualizada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def reactivar_alerta(tipo, id_referencia, subtipo='general'):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            NotificacionesService._asegurar_tabla_alertas(cursor)
            cursor.execute("""
                DELETE FROM tb_alertas_ignoradas 
                WHERE tipo = %s AND id_referencia = %s AND subtipo = %s
            """, (tipo, id_referencia, subtipo))
            conexion.commit()
            return {"success": True, "message": "Alerta reactivada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def limpiar_resueltas():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            NotificacionesService._asegurar_tabla_alertas(cursor)
            cursor.execute("UPDATE tb_alertas_ignoradas SET limpiado = 1 WHERE COALESCE(limpiado, 0) = 0")
            afectadas = cursor.rowcount
            conexion.commit()
            return {"success": True, "message": "Sección de resueltas y omitidas limpiada correctamente", "afectadas": afectadas}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def obtener_avisos_y_pendientes():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ahora = datetime.date.today()
            NotificacionesService._asegurar_tabla_alertas(cursor)

            # Obtener alertas resueltas / omitidas para excluirlas de activas
            cursor.execute("""
                SELECT id, tipo, id_referencia, subtipo, accion, motivo, nombre, cct, grupo, usuario, limpiado, created_at 
                FROM tb_alertas_ignoradas 
                ORDER BY created_at DESC
            """)
            filas_ignoradas = cursor.fetchall()
            set_ignoradas = {(r['tipo'], r['id_referencia']) for r in filas_ignoradas}
            set_ignoradas_subtipos = {(r['tipo'], r['id_referencia'], r['subtipo']) for r in filas_ignoradas}

            # 1. DOCUMENTOS FALTANTES / EXPIRADOS
            # Alumnos con certificado incompleto expirado o sin boleta
            cursor.execute("""
                SELECT 
                    a.idAlumno,
                    CONCAT_WS(' ', a.nombre, a.apPaterno, a.apMaterno) AS nombreAlumno,
                    a.numeroControl AS matricula,
                    a.statusAlumno,
                    a.certificado_incompleto,
                    a.fecha_entrega_certificado,
                    a.trae_boleta,
                    a.observaciones,
                    nei.numero AS nivel_ingreso_num,
                    COALESCE(gr.clave, 'Sin Grupo') AS nombreGrupo,
                    ct.nombre AS nombreCentroTrabajo
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON COALESCE(gr.id_centroTrabajo, a.id_nivel_ingreso) = ct.id
                LEFT JOIN tb_niveles_academicos nei ON a.id_nivel_ingreso = nei.id
                WHERE a.statusAlumno NOT IN ('BAJA_DEFINITIVA', 'INACTIVO')
                  AND (
                      (a.certificado_incompleto = 'SI' AND (a.fecha_entrega_certificado IS NULL OR a.fecha_entrega_certificado <= CURRENT_DATE))
                      OR (
                          a.trae_boleta = 'NO'
                          AND nei.numero > 1
                          AND (a.observaciones IS NULL OR a.observaciones NOT LIKE '%[REGISTRO_HISTORICO]%')
                      )
                  )
                ORDER BY a.apPaterno ASC, a.nombre ASC
            """)
            alumnos_docs = cursor.fetchall()
            
            alertas_documentos = []
            for al in alumnos_docs:
                if ('documentos', al['idAlumno']) in set_ignoradas:
                    continue

                detalle = []
                es_critico = False
                subtipo = 'general'
                
                if al["certificado_incompleto"] == "SI":
                    subtipo = 'certificado'
                    if al["fecha_entrega_certificado"]:
                        fecha_limite = al["fecha_entrega_certificado"]
                        if isinstance(fecha_limite, str):
                            try:
                                fecha_limite = datetime.datetime.strptime(fecha_limite, "%Y-%m-%d").date()
                            except ValueError:
                                pass
                        
                        if isinstance(fecha_limite, datetime.date):
                            dias_vencido = (ahora - fecha_limite).days
                            if dias_vencido >= 0:
                                es_critico = True
                                detalle.append(f"Certificado parcial incompleto vencido hace {dias_vencido} días (Límite: {fecha_limite.strftime('%d/%m/%Y')})")
                            else:
                                detalle.append(f"Pendiente Certificado parcial (Límite: {fecha_limite.strftime('%d/%m/%Y')})")
                        else:
                            detalle.append(f"Pendiente Certificado parcial (Límite: {fecha_limite})")
                    else:
                        es_critico = True
                        detalle.append("Falta Certificado parcial (Sin fecha límite registrada)")
                        
                nivel_num = al.get("nivel_ingreso_num")
                obs = al.get("observaciones") or ""
                es_historico = "[REGISTRO_HISTORICO]" in obs
                if al["trae_boleta"] == "NO" and nivel_num is not None and nivel_num > 1 and not es_historico:
                    subtipo = 'boleta' if not detalle else 'general'
                    detalle.append("Falta Boleta de calificaciones anteriores")
                    
                alertas_documentos.append({
                    "idAlumno": al["idAlumno"],
                    "nombre": al["nombreAlumno"],
                    "matricula": al["matricula"] or "Sin Matrícula",
                    "statusAlumno": al["statusAlumno"],
                    "grupo": al["nombreGrupo"],
                    "cct": al["nombreCentroTrabajo"] or "BGNE",
                    "detalle": " y ".join(detalle),
                    "subtipo": subtipo,
                    "esCritico": es_critico
                })

            # 2. TRÁMITES DE EQUIVALENCIA
            # Alumnos que requieren equivalencia
            cursor.execute("""
                SELECT 
                    a.idAlumno,
                    CONCAT_WS(' ', a.nombre, a.apPaterno, a.apMaterno) AS nombreAlumno,
                    a.numeroControl AS matricula,
                    a.statusAlumno,
                    a.equivalencia,
                    a.estado_pago_equivalencia,
                    COALESCE(gr.clave, 'Sin Grupo') AS nombreGrupo,
                    ct.nombre AS nombreCentroTrabajo
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON COALESCE(gr.id_centroTrabajo, a.id_nivel_ingreso) = ct.id
                WHERE a.statusAlumno NOT IN ('BAJA_DEFINITIVA')
                  AND a.equivalencia = 'SI'
                ORDER BY a.apPaterno ASC, a.nombre ASC
            """)
            alumnos_equiv = cursor.fetchall()
            
            alertas_equivalencias = []
            for al in alumnos_equiv:
                if ('equivalencias', al['idAlumno']) in set_ignoradas:
                    continue

                pago_status = al["estado_pago_equivalencia"] or "PENDIENTE"
                
                if pago_status == "PENDIENTE":
                    tipo_alerta = "pago_pendiente"
                    detalle = "Trámite de equivalencia: Pendiente de pago"
                    es_critico = False
                else:
                    tipo_alerta = "tramite_sep"
                    detalle = "Pago recibido. Control Escolar debe ingresar el trámite de equivalencia ante la SEP"
                    es_critico = True
                    
                alertas_equivalencias.append({
                    "idAlumno": al["idAlumno"],
                    "nombre": al["nombreAlumno"],
                    "matricula": al["matricula"] or "Sin Matrícula",
                    "statusAlumno": al["statusAlumno"],
                    "grupo": al["nombreGrupo"],
                    "cct": al["nombreCentroTrabajo"] or "BGNE",
                    "tipo": tipo_alerta,
                    "subtipo": "equivalencia",
                    "detalle": detalle,
                    "esCritico": es_critico
                })

            # 3. GRUPOS: EVALUACIÓN DE TÉRMINO, FALTA DE HORARIO Y MATERIAS INCOMPLETAS
            from app.services.periodos_academico import PeriodoAcademicoService

            cursor.execute("""
                SELECT 
                    g.id AS idGrupo,
                    g.clave AS claveGrupo,
                    g.fechaInicio,
                    g.fechaFin,
                    g.id_centroTrabajo,
                    ct.nombre AS nombreCentroTrabajo,
                    g.id_tipoPeriodo,
                    g.id_nivel_academico,
                    na.nombre AS nombre_nivel,
                    g.statusGrupo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                LEFT JOIN tb_niveles_academicos na ON g.id_nivel_academico = na.id
                WHERE (g.statusGrupo = 'ACTIVO' OR g.statusGrupo IS NULL)
                ORDER BY g.fechaFin ASC, g.id ASC
            """)
            grupos_activos = cursor.fetchall()

            alertas_grupos = []

            for g in grupos_activos:
                id_grupo = g["idGrupo"]
                cct_id = g["id_centroTrabajo"]
                es_bgne = (cct_id == 3 or g.get("id_tipoPeriodo") == 2)
                cct_nombre = g["nombreCentroTrabajo"] or ("BGNE" if es_bgne else "BTI")

                # 1. Nivel actual y fechas efectivas
                res_nivel = PeriodoAcademicoService.calcularNivelGrupo(id_grupo)
                nivel_actual_id = (res_nivel.get("id_nivel_academico") if res_nivel else None) or g["id_nivel_academico"]
                fecha_fin_eval = (res_nivel.get("fechaFinNivel") if res_nivel else None) or g["fechaFin"]
                fecha_inicio_eval = (res_nivel.get("fechaInicioNivel") if res_nivel else None) or g["fechaInicio"]

                nombre_nivel = g.get("nombre_nivel")
                if not nombre_nivel and nivel_actual_id:
                    cursor.execute("SELECT nombre FROM tb_niveles_academicos WHERE id = %s", (nivel_actual_id,))
                    n_row = cursor.fetchone()
                    if n_row:
                        nombre_nivel = n_row["nombre"] if isinstance(n_row, dict) else n_row[0]
                if not nombre_nivel:
                    nombre_nivel = f"Nivel {nivel_actual_id}" if nivel_actual_id else "Nivel Asignado"

                # 2. Materias requeridas del nivel actual
                materias_req_actual = []
                if nivel_actual_id:
                    cursor.execute("""
                        SELECT id, nombreMateria 
                        FROM tb_materias 
                        WHERE id_nivel_academico = %s 
                          AND (idCentroTrabajo = %s OR idCentroTrabajo IS NULL)
                          AND (estatusMateria = 'ACTIVA' OR estatusMateria IS NULL)
                        ORDER BY orden ASC, id ASC
                    """, (nivel_actual_id, cct_id))
                    materias_req_actual = cursor.fetchall()

                req_actual_dict = {
                    (m["id"] if isinstance(m, dict) else m[0]): (m["nombreMateria"] if isinstance(m, dict) else m[1])
                    for m in materias_req_actual
                }

                # 3. Materias programadas en horario regular (es_prehorario=0) y pre-horario (es_prehorario=1)
                cursor.execute("""
                    SELECT DISTINCT h.id_materia, m.nombreMateria, m.id_nivel_academico, h.es_prehorario
                    FROM tb_horarios h
                    JOIN tb_materias m ON h.id_materia = m.id
                    WHERE h.id_grupo = %s
                """, (id_grupo,))
                horarios_rows = cursor.fetchall()

                sched_regulares_ids = set()
                sched_prehorario_ids = set()
                for h in horarios_rows:
                    mid = h["id_materia"] if isinstance(h, dict) else h[0]
                    es_pre = h["es_prehorario"] if isinstance(h, dict) else h[3]
                    if int(es_pre or 0) == 1:
                        sched_prehorario_ids.add(mid)
                    else:
                        sched_regulares_ids.add(mid)

                total_clases_programadas = len(sched_regulares_ids) + len(sched_prehorario_ids)

                # 4. Cálculo de días restantes
                if isinstance(fecha_fin_eval, str):
                    try:
                        fecha_fin_eval = datetime.datetime.strptime(fecha_fin_eval, "%Y-%m-%d").date()
                    except ValueError:
                        pass

                dias_restantes = None
                fecha_fin_str = str(fecha_fin_eval)
                if isinstance(fecha_fin_eval, datetime.date):
                    dias_restantes = (fecha_fin_eval - ahora).days
                    fecha_fin_str = fecha_fin_eval.strftime("%d/%m/%Y")

                # 5. Siguiente nivel académico y sus materias
                next_nivel_id = None
                if nivel_actual_id:
                    if es_bgne and nivel_actual_id < 6:
                        next_nivel_id = nivel_actual_id + 1
                    elif not es_bgne and nivel_actual_id < 12:
                        next_nivel_id = nivel_actual_id + 1

                next_req_dict = {}
                next_nivel_nom = None
                if next_nivel_id:
                    cursor.execute("""
                        SELECT id, nombreMateria 
                        FROM tb_materias 
                        WHERE id_nivel_academico = %s 
                          AND (idCentroTrabajo = %s OR idCentroTrabajo IS NULL)
                          AND (estatusMateria = 'ACTIVA' OR estatusMateria IS NULL)
                        ORDER BY orden ASC, id ASC
                    """, (next_nivel_id, cct_id))
                    mats_next_rows = cursor.fetchall()
                    next_req_dict = {
                        (m["id"] if isinstance(m, dict) else m[0]): (m["nombreMateria"] if isinstance(m, dict) else m[1])
                        for m in mats_next_rows
                    }

                    cursor.execute("SELECT nombre FROM tb_niveles_academicos WHERE id = %s", (next_nivel_id,))
                    n_next_row = cursor.fetchone()
                    if n_next_row:
                        next_nivel_nom = n_next_row["nombre"] if isinstance(n_next_row, dict) else n_next_row[0]
                    else:
                        next_nivel_nom = f"Nivel {next_nivel_id}"

                all_assigned_ids = sched_regulares_ids.union(sched_prehorario_ids)
                next_cubiertas = all_assigned_ids.intersection(next_req_dict.keys())
                horario_siguiente_armado = (len(next_cubiertas) >= len(next_req_dict) and len(next_req_dict) > 0)

                # --- ALERTA 1: GRUPO SIN NINGÚN HORARIO ---
                if total_clases_programadas == 0:
                    subtipo = "sin_horario"
                    if ('grupos', id_grupo, subtipo) not in set_ignoradas_subtipos and ('grupos', id_grupo, 'general') not in set_ignoradas_subtipos:
                        mats_nombres = list(req_actual_dict.values())
                        if len(mats_nombres) > 4:
                            str_mats = ", ".join(mats_nombres[:4]) + f" y {len(mats_nombres)-4} materias más"
                        elif mats_nombres:
                            str_mats = ", ".join(mats_nombres)
                        else:
                            str_mats = "materias del plan"

                        detalle = f"El grupo no cuenta con horario asignado. Un grupo no puede estar sin horario ni materias registradas. Debe cursar {nombre_nivel} ({str_mats})."
                        alertas_grupos.append({
                            "idGrupo": id_grupo,
                            "clave": g["claveGrupo"],
                            "cct": cct_nombre,
                            "tipo": "sin_horario",
                            "subtipo": subtipo,
                            "badge_tipo": "Sin Horario",
                            "badge_color": "bg-danger text-white",
                            "icono": "bi-calendar-x-fill text-danger",
                            "fechaFin": fecha_fin_str,
                            "diasRestantes": dias_restantes,
                            "detalle": detalle,
                            "esCritico": True,
                            "id_centroTrabajo": cct_id,
                            "accion_tipo": "armar_horario",
                            "es_prehorario": 0
                        })

                # --- ALERTA 2: HORARIO INCOMPLETO (FALTAN MATERIAS POR INDICAR) ---
                elif len(req_actual_dict) > 0:
                    cubiertas_actual = sched_regulares_ids.intersection(req_actual_dict.keys())
                    faltantes_actual = [
                        nom for mid, nom in req_actual_dict.items() 
                        if mid not in sched_regulares_ids
                    ]
                    if faltantes_actual:
                        subtipo = "materias_incompletas"
                        if ('grupos', id_grupo, subtipo) not in set_ignoradas_subtipos and ('grupos', id_grupo, 'general') not in set_ignoradas_subtipos:
                            str_faltantes = ", ".join(faltantes_actual)
                            detalle = f"Horario incompleto ({len(cubiertas_actual)} de {len(req_actual_dict)} materias indicadas para {nombre_nivel}). Faltan por programar: {str_faltantes}."
                            alertas_grupos.append({
                                "idGrupo": id_grupo,
                                "clave": g["claveGrupo"],
                                "cct": cct_nombre,
                                "tipo": "materias_incompletas",
                                "subtipo": subtipo,
                                "badge_tipo": "Horario Incompleto",
                                "badge_color": "bg-warning text-dark",
                                "icono": "bi-exclamation-diamond-fill text-warning",
                                "fechaFin": fecha_fin_str,
                                "diasRestantes": dias_restantes,
                                "detalle": detalle,
                                "esCritico": (len(cubiertas_actual) == 0),
                                "id_centroTrabajo": cct_id,
                                "accion_tipo": "completar_horario",
                                "es_prehorario": 0
                            })

                # --- ALERTA 3: CICLO TERMINADO O PRÓXIMO A TERMINAR Y AÚN NO SE HA ARMADO SU HORARIO ---
                if dias_restantes is not None and dias_restantes <= 30:
                    if dias_restantes < 0:
                        dias_venc = -dias_restantes
                        badge_tipo = "Ciclo Vencido"
                        badge_color = "bg-danger text-white"
                        icono = "bi-exclamation-triangle-fill text-danger"
                        es_critico = True
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluyó hace {dias_venc} días ({fecha_fin_str})."
                    elif dias_restantes == 0:
                        badge_tipo = "Concluye Hoy"
                        badge_color = "bg-danger text-white"
                        icono = "bi-alarm-fill text-danger"
                        es_critico = True
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluye hoy {fecha_fin_str}."
                    elif 1 <= dias_restantes <= 7:
                        badge_tipo = "Término Ciclo"
                        badge_color = "bg-warning text-dark"
                        icono = "bi-clock-history text-warning"
                        es_critico = True
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluye el {fecha_fin_str} (falta 1 semana o menos: {dias_restantes} días)."
                    elif 8 <= dias_restantes <= 14:
                        badge_tipo = "Término Ciclo"
                        badge_color = "bg-info text-dark"
                        icono = "bi-clock-history text-info"
                        es_critico = False
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluye el {fecha_fin_str} (faltan 2 semanas: {dias_restantes} días)."
                    elif 15 <= dias_restantes <= 21:
                        badge_tipo = "Término Ciclo"
                        badge_color = "bg-info text-dark"
                        icono = "bi-clock-history text-info"
                        es_critico = False
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluye el {fecha_fin_str} (faltan 3 semanas: {dias_restantes} días)."
                    else:
                        badge_tipo = "Término Ciclo"
                        badge_color = "bg-info text-dark"
                        icono = "bi-clock-history text-info"
                        es_critico = False
                        tiempo_msg = f"El ciclo de {nombre_nivel} concluye el {fecha_fin_str} (faltan {dias_restantes} días)."

                    if next_nivel_id:
                        mats_next_nombres = list(next_req_dict.values())
                        if len(mats_next_nombres) > 4:
                            str_mats_next = ", ".join(mats_next_nombres[:4]) + f" y {len(mats_next_nombres)-4} más"
                        elif mats_next_nombres:
                            str_mats_next = ", ".join(mats_next_nombres)
                        else:
                            str_mats_next = "materias correspondientes"

                        if not horario_siguiente_armado:
                            subtipo = "termino_sin_horario"
                            if ('grupos', id_grupo, subtipo) not in set_ignoradas_subtipos and ('grupos', id_grupo, 'general') not in set_ignoradas_subtipos:
                                detalle_termino = f"{tiempo_msg} [ATENCIÓN: Aún no se ha armado el horario para el siguiente periodo ({next_nivel_nom})]. Materias a cursar: {str_mats_next}."
                                alertas_grupos.append({
                                    "idGrupo": id_grupo,
                                    "clave": g["claveGrupo"],
                                    "cct": cct_nombre,
                                    "tipo": "termino_sin_horario",
                                    "subtipo": subtipo,
                                    "badge_tipo": badge_tipo,
                                    "badge_color": badge_color,
                                    "icono": icono,
                                    "fechaFin": fecha_fin_str,
                                    "diasRestantes": dias_restantes,
                                    "detalle": detalle_termino,
                                    "esCritico": es_critico,
                                    "id_centroTrabajo": cct_id,
                                    "accion_tipo": "armar_prehorario" if es_bgne else "armar_horario",
                                    "es_prehorario": 1 if es_bgne else 0
                                })
                        else:
                            subtipo = "termino_ciclo"
                            if ('grupos', id_grupo, subtipo) not in set_ignoradas_subtipos and ('grupos', id_grupo, 'general') not in set_ignoradas_subtipos:
                                detalle_termino = f"{tiempo_msg} El horario para {next_nivel_nom} ya se encuentra armado."
                                alertas_grupos.append({
                                    "idGrupo": id_grupo,
                                    "clave": g["claveGrupo"],
                                    "cct": cct_nombre,
                                    "tipo": "termino_ciclo",
                                    "subtipo": subtipo,
                                    "badge_tipo": badge_tipo,
                                    "badge_color": "bg-secondary text-white" if dias_restantes >= 0 else badge_color,
                                    "icono": "bi-calendar-check text-secondary",
                                    "fechaFin": fecha_fin_str,
                                    "diasRestantes": dias_restantes,
                                    "detalle": detalle_termino,
                                    "esCritico": False,
                                    "id_centroTrabajo": cct_id,
                                    "accion_tipo": "captura_notas",
                                    "es_prehorario": 0
                                })
                    else:
                        subtipo = "termino_ciclo"
                        if ('grupos', id_grupo, subtipo) not in set_ignoradas_subtipos and ('grupos', id_grupo, 'general') not in set_ignoradas_subtipos:
                            detalle_termino = f"{tiempo_msg} Conclusión definitiva de estudios de bachillerato ({nombre_nivel}). Generación lista para captura de actas y certificados."
                            alertas_grupos.append({
                                "idGrupo": id_grupo,
                                "clave": g["claveGrupo"],
                                "cct": cct_nombre,
                                "tipo": "termino_ciclo",
                                "subtipo": subtipo,
                                "badge_tipo": "Fin de Generación" if dias_restantes >= 0 else "Generación Egresada",
                                "badge_color": "bg-primary text-white",
                                "icono": "bi-mortarboard-fill text-primary",
                                "fechaFin": fecha_fin_str,
                                "diasRestantes": dias_restantes,
                                "detalle": detalle_termino,
                                "esCritico": es_critico,
                                "id_centroTrabajo": cct_id,
                                "accion_tipo": "captura_notas",
                                "es_prehorario": 0
                            })

            # 4. NUEVOS ALUMNOS REGISTRADOS (Alerta para el Administrador)
            try:
                # Ajuste de retrocompatibilidad: convertir a hora local México registros guardados en UTC
                cursor.execute("""
                    UPDATE tb_alumnos 
                    SET createAt = DATE_SUB(createAt, INTERVAL 6 HOUR) 
                    WHERE createAt >= '2026-09-26 18:00:00' 
                      AND createAt <= '2026-09-27 06:00:00'
                """)
                conexion.commit()
            except Exception:
                pass

            cursor.execute("""
                SELECT 
                    a.idAlumno,
                    CONCAT_WS(' ', a.nombre, a.apPaterno, a.apMaterno) AS nombreAlumno,
                    a.numeroControl AS matricula,
                    a.createBy,
                    a.createAt,
                    a.idGrupo,
                    COALESCE(gr.clave, 'Sin Grupo') AS nombreGrupo,
                    COALESCE(ct.nombre, 'Sin CCT') AS nombreCentroTrabajo
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON COALESCE(gr.id_centroTrabajo, a.id_nivel_ingreso) = ct.id
                WHERE a.createAt IS NOT NULL
                  AND a.createAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY a.createAt DESC, a.idAlumno DESC
            """)
            nuevos_alumnos_rows = cursor.fetchall()
            
            alertas_nuevos_alumnos = []
            now_mx = get_mexico_now().replace(tzinfo=None)
            for al in nuevos_alumnos_rows:
                id_al = al["idAlumno"]
                subtipo = "nuevo_registro"
                if ('nuevos_alumnos', id_al, subtipo) in set_ignoradas_subtipos or ('nuevos_alumnos', id_al) in set_ignoradas:
                    continue

                creador = al["createBy"] or "Personal Escolar"
                f_creacion = al["createAt"]

                if hasattr(f_creacion, "strftime"):
                    dt_creacion = f_creacion.replace(tzinfo=None) if hasattr(f_creacion, "tzinfo") and f_creacion.tzinfo else f_creacion
                    # Salvaguarda: Si la fecha está en el futuro respecto a la hora local de México (indicando registro guardado en UTC)
                    if dt_creacion > now_mx:
                        dt_creacion = dt_creacion - datetime.timedelta(hours=6)
                    fecha_str = dt_creacion.strftime("%d/%m/%Y")
                    hora_str = dt_creacion.strftime("%H:%M:%S")
                else:
                    fecha_str = str(f_creacion)
                    hora_str = ""
                
                hora_txt = f" a las {hora_str}" if hora_str else ""
                detalle = f"Registrado por el usuario '{creador}' en el grupo {al['nombreGrupo']} ({al['nombreCentroTrabajo']}) el {fecha_str}{hora_txt}."

                alertas_nuevos_alumnos.append({
                    "idAlumno": id_al,
                    "nombre": al["nombreAlumno"],
                    "matricula": al["matricula"] or "Sin Matrícula",
                    "creador": creador,
                    "grupo": al["nombreGrupo"],
                    "cct": al["nombreCentroTrabajo"],
                    "fecha_creacion": fecha_str,
                    "hora_creacion": hora_str,
                    "detalle": detalle,
                    "tipo": "nuevos_alumnos",
                    "subtipo": subtipo,
                    "badge_tipo": "Nuevo Alumno",
                    "badge_color": "bg-success text-white",
                    "icono": "bi-person-plus-fill text-success",
                    "esCritico": False
                })

            # 5. LISTADO DE ALERTAS RESUELTAS / OMITIDAS (solo no limpiadas)
            alertas_resueltas = []
            for r in filas_ignoradas:
                if r.get("limpiado") == 1 or r.get("limpiado") == "1":
                    continue
                fecha_str = r["created_at"].strftime("%d/%m/%Y %H:%M") if hasattr(r["created_at"], "strftime") else str(r["created_at"])
                alertas_resueltas.append({
                    "id": r["id"],
                    "tipo": r["tipo"],
                    "id_referencia": r["id_referencia"],
                    "subtipo": r["subtipo"],
                    "accion": r["accion"],
                    "motivo": r["motivo"] or ("Resuelto" if r["accion"] == "resuelto" else "Omitido / No es alerta"),
                    "nombre": r["nombre"] or "Alumno / Grupo",
                    "cct": r["cct"] or "—",
                    "grupo": r["grupo"] or "—",
                    "usuario": r["usuario"] or "Administrador",
                    "fecha": fecha_str
                })

            return {
                "success": True,
                "data": {
                    "documentos": alertas_documentos,
                    "equivalencias": alertas_equivalencias,
                    "grupos": alertas_grupos,
                    "nuevos_alumnos": alertas_nuevos_alumnos,
                    "resueltas": alertas_resueltas,
                    "totales": {
                        "documentos": len(alertas_documentos),
                        "equivalencias": len(alertas_equivalencias),
                        "grupos": len(alertas_grupos),
                        "nuevos_alumnos": len(alertas_nuevos_alumnos),
                        "resueltas": len(alertas_resueltas),
                        "total": len(alertas_documentos) + len(alertas_equivalencias) + len(alertas_grupos) + len(alertas_nuevos_alumnos)
                    }
                }
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
