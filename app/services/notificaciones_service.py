import datetime
from app.config.conexion import get_connection

class NotificacionesService:
    @staticmethod
    def obtener_avisos_y_pendientes():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            ahora = datetime.date.today()

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
                    COALESCE(gr.clave, 'Sin Grupo') AS nombreGrupo,
                    ct.nombre AS nombreCentroTrabajo
                FROM tb_alumnos a
                LEFT JOIN tb_grupos gr ON a.idGrupo = gr.id
                LEFT JOIN tb_centrotrabajo ct ON COALESCE(gr.id_centroTrabajo, a.id_nivel_ingreso) = ct.id
                WHERE a.statusAlumno NOT IN ('BAJA_DEFINITIVA', 'INACTIVO')
                  AND (
                      (a.certificado_incompleto = 'SI' AND (a.fecha_entrega_certificado IS NULL OR a.fecha_entrega_certificado <= CURRENT_DATE))
                      OR a.trae_boleta = 'NO'
                  )
                ORDER BY a.apPaterno ASC, a.nombre ASC
            """)
            alumnos_docs = cursor.fetchall()
            
            alertas_documentos = []
            for al in alumnos_docs:
                detalle = []
                es_critico = False
                
                if al["certificado_incompleto"] == "SI":
                    if al["fecha_entrega_certificado"]:
                        fecha_limite = al["fecha_entrega_certificado"]
                        # Convert to date if it is a string or datetime
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
                        
                if al["trae_boleta"] == "NO":
                    detalle.append("Falta Boleta de calificaciones anteriores")
                    
                alertas_documentos.append({
                    "idAlumno": al["idAlumno"],
                    "nombre": al["nombreAlumno"],
                    "matricula": al["matricula"] or "Sin Matrícula",
                    "statusAlumno": al["statusAlumno"],
                    "grupo": al["nombreGrupo"],
                    "cct": al["nombreCentroTrabajo"] or "BGNE",
                    "detalle": " y ".join(detalle),
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
                pago_status = al["estado_pago_equivalencia"] or "PENDIENTE"
                
                if pago_status == "PENDIENTE":
                    tipo_alerta = "pago_pendiente"
                    detalle = "Trámite de equivalencia: Pendiente de pago"
                    es_critico = False
                else:
                    tipo_alerta = "tramite_sep"
                    detalle = "Pago recibido. Control Escolar debe ingresar el trámite de equivalencia ante la SEP"
                    es_critico = True # Control escolar needs to act
                    
                alertas_equivalencias.append({
                    "idAlumno": al["idAlumno"],
                    "nombre": al["nombreAlumno"],
                    "matricula": al["matricula"] or "Sin Matrícula",
                    "statusAlumno": al["statusAlumno"],
                    "grupo": al["nombreGrupo"],
                    "cct": al["nombreCentroTrabajo"] or "BGNE",
                    "tipo": tipo_alerta,
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
                
                # Clasificar semanas restantes
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

                # Si es un grupo de BGNE (id_centroTrabajo == 3)
                if g["id_centroTrabajo"] == 3:
                    detalle += " [ATENCIÓN: Se debe armar el nuevo horario para el grupo]"

                alertas_grupos.append({
                    "idGrupo": g["idGrupo"],
                    "clave": g["claveGrupo"],
                    "cct": g["nombreCentroTrabajo"] or "BGNE",
                    "fechaFin": fecha_fin_str,
                    "diasRestantes": dias_restantes,
                    "detalle": detalle,
                    "id_centroTrabajo": g["id_centroTrabajo"]
                })

            return {
                "success": True,
                "data": {
                    "documentos": alertas_documentos,
                    "equivalencias": alertas_equivalencias,
                    "grupos": alertas_grupos,
                    "totales": {
                        "documentos": len(alertas_documentos),
                        "equivalencias": len(alertas_equivalencias),
                        "grupos": len(alertas_grupos),
                        "total": len(alertas_documentos) + len(alertas_equivalencias) + len(alertas_grupos)
                    }
                }
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()
