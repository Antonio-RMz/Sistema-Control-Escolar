import datetime
from app.config.conexion import get_connection

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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_alerta (tipo, id_referencia, subtipo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

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
            if tipo in ('documentos', 'equivalencias'):
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

            # Registrar en tb_alertas_ignoradas
            cursor.execute("""
                INSERT INTO tb_alertas_ignoradas 
                (tipo, id_referencia, subtipo, accion, motivo, nombre, cct, grupo, usuario, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    accion = VALUES(accion),
                    motivo = VALUES(motivo),
                    nombre = VALUES(nombre),
                    cct = VALUES(cct),
                    grupo = VALUES(grupo),
                    usuario = VALUES(usuario),
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
    def obtener_avisos_y_pendientes():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ahora = datetime.date.today()
            NotificacionesService._asegurar_tabla_alertas(cursor)

            # Obtener alertas resueltas / omitidas para excluirlas de activas
            cursor.execute("""
                SELECT id, tipo, id_referencia, subtipo, accion, motivo, nombre, cct, grupo, usuario, created_at 
                FROM tb_alertas_ignoradas 
                ORDER BY created_at DESC
            """)
            filas_ignoradas = cursor.fetchall()
            set_ignoradas = {(r['tipo'], r['id_referencia']) for r in filas_ignoradas}

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

            # 3. GRUPOS PRÓXIMOS A TERMINAR (Próximos 30 días)
            cursor.execute("""
                SELECT 
                    g.id AS idGrupo,
                    g.clave AS claveGrupo,
                    g.fechaInicio,
                    g.fechaFin,
                    ct.nombre AS nombreCentroTrabajo,
                    g.id_centroTrabajo
                FROM tb_grupos g
                LEFT JOIN tb_centrotrabajo ct ON g.id_centroTrabajo = ct.id
                WHERE (g.statusGrupo = 'ACTIVO' OR g.statusGrupo IS NULL)
                  AND g.fechaFin >= CURRENT_DATE
                  AND g.fechaFin <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
                ORDER BY g.fechaFin ASC
            """)
            grupos_termino = cursor.fetchall()
            
            alertas_grupos = []
            for g in grupos_termino:
                if ('grupos', g['idGrupo']) in set_ignoradas:
                    continue

                fecha_fin = g["fechaFin"]
                if isinstance(fecha_fin, str):
                    try:
                        fecha_fin = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                
                dias_restantes = 0
                if isinstance(fecha_fin, datetime.date):
                    dias_restantes = (fecha_fin - ahora).days
                    fecha_fin_str = fecha_fin.strftime("%d/%m/%Y")
                else:
                    fecha_fin_str = str(fecha_fin)
                
                if 15 <= dias_restantes <= 21:
                    semanas_msg = "Faltan 3 semanas para concluir el ciclo."
                elif 8 <= dias_restantes <= 14:
                    semanas_msg = "Faltan 2 semanas para concluir el ciclo."
                elif 0 <= dias_restantes <= 7:
                    semanas_msg = "Falta 1 semana o menos para concluir el ciclo."
                elif dias_restantes < 0:
                    semanas_msg = f"Ciclo vencido hace {-dias_restantes} días."
                else:
                    semanas_msg = f"Faltan {dias_restantes} días para concluir el ciclo."

                detalle = f"El ciclo del grupo concluye el {fecha_fin_str}. {semanas_msg}"

                if g["id_centroTrabajo"] == 3:
                    detalle += " [ATENCIÓN: Se debe armar el nuevo horario para el grupo]"

                alertas_grupos.append({
                    "idGrupo": g["idGrupo"],
                    "clave": g["claveGrupo"],
                    "cct": g["nombreCentroTrabajo"] or "BGNE",
                    "fechaFin": fecha_fin_str,
                    "diasRestantes": dias_restantes,
                    "detalle": detalle,
                    "subtipo": "termino_ciclo",
                    "id_centroTrabajo": g["id_centroTrabajo"]
                })

            # 4. LISTADO DE ALERTAS RESUELTAS / OMITIDAS
            alertas_resueltas = []
            for r in filas_ignoradas:
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
                    "resueltas": alertas_resueltas,
                    "totales": {
                        "documentos": len(alertas_documentos),
                        "equivalencias": len(alertas_equivalencias),
                        "grupos": len(alertas_grupos),
                        "resueltas": len(alertas_resueltas),
                        "total": len(alertas_documentos) + len(alertas_equivalencias) + len(alertas_grupos)
                    }
                }
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
