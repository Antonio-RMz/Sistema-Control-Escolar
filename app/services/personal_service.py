from app.config.conexion import get_connection
import pymysql

class PersonalService:
    @staticmethod
    def get_personales(page, limit, search, status):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            offset = (page - 1) * limit
            sql = """
                SELECT 
                    idPersonal, 
                    nombre, 
                    usuario, 
                    rol, 
                    permisos_modulos, 
                    status,
                    idBiometrico,
                    es_servicio_social,
                    horas_objetivo,
                    createAt,
                    updateAt
                FROM tb_personal
                WHERE 1=1
            """
            params = []
            if search:
                sql += " AND (nombre LIKE %s OR usuario LIKE %s OR rol LIKE %s OR idBiometrico LIKE %s)"
                like = f"%{search}%"
                params.extend([like, like, like, like])
            if status:
                sql += " AND status = %s"
                params.append(status)
            
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            data = cursor.fetchall()
            return {"data": data, "page": page, "limit": limit}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_personal(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            usuario = data.get("usuario").strip()
            # Validar usuario duplicado
            cursor.execute("SELECT idPersonal FROM tb_personal WHERE usuario = %s", (usuario,))
            if cursor.fetchone():
                return {"error": "El nombre de usuario ya está asignado a otra cuenta de personal"}

            # Validar idBiometrico duplicado
            id_bio = data.get("idBiometrico")
            if id_bio is not None and str(id_bio).strip() != "":
                id_bio = str(id_bio).strip()
                cursor.execute("SELECT idPersonal, nombre FROM tb_personal WHERE idBiometrico = %s", (id_bio,))
                p_dup = cursor.fetchone()
                if p_dup:
                    return {"error": f"El ID Biométrico '{id_bio}' ya está asignado al personal '{p_dup['nombre']}'."}

                cursor.execute("SELECT idDocente, nombreDocente FROM tb_docentes WHERE idBiometrico = %s", (id_bio,))
                d_dup = cursor.fetchone()
                if d_dup:
                    return {"error": f"El ID Biométrico '{id_bio}' ya está asignado al docente '{d_dup['nombreDocente']}'."}
            else:
                id_bio = None
            
            permisos_modulos = data.get("permisos_modulos")
            if isinstance(permisos_modulos, list):
                permisos_modulos = ",".join(permisos_modulos)
            elif not permisos_modulos:
                permisos_modulos = "inicio,notificaciones,alumnos,docentes,grupos,materias,planes,formatos,generaciones"

            query = """
                INSERT INTO tb_personal (nombre, usuario, password, rol, permisos_modulos, status, idBiometrico, es_servicio_social, horas_objetivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    data.get("nombre"),
                    usuario,
                    data.get("password"),
                    data.get("rol"),
                    permisos_modulos,
                    data.get("status", "ACTIVO"),
                    id_bio,
                    data.get("es_servicio_social", 0),
                    data.get("horas_objetivo")
                )
            )
            conexion.commit()
            return {"success": True, "idPersonal": cursor.lastrowid}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_personal_by_id(id_personal):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT idPersonal, nombre, usuario, rol, permisos_modulos, status, idBiometrico, es_servicio_social, horas_objetivo, createAt, updateAt
                FROM tb_personal
                WHERE idPersonal = %s
            """, (id_personal,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update_personal(id_personal, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            usuario = data.get("usuario").strip()
            # Validar usuario duplicado
            cursor.execute("SELECT idPersonal FROM tb_personal WHERE usuario = %s AND idPersonal != %s", (usuario, id_personal))
            if cursor.fetchone():
                return {"error": "El nombre de usuario ya está asignado a otra cuenta de personal"}

            # Validar idBiometrico duplicado
            id_bio = data.get("idBiometrico")
            if id_bio is not None and str(id_bio).strip() != "":
                id_bio = str(id_bio).strip()
                cursor.execute("SELECT idPersonal, nombre FROM tb_personal WHERE idBiometrico = %s AND idPersonal != %s", (id_bio, id_personal))
                p_dup = cursor.fetchone()
                if p_dup:
                    return {"error": f"El ID Biométrico '{id_bio}' ya está asignado al personal '{p_dup['nombre']}'."}

                cursor.execute("SELECT idDocente, nombreDocente FROM tb_docentes WHERE idBiometrico = %s", (id_bio,))
                d_dup = cursor.fetchone()
                if d_dup:
                    return {"error": f"El ID Biométrico '{id_bio}' ya está asignado al docente '{d_dup['nombreDocente']}'."}
            else:
                id_bio = None
            
            permisos_modulos = data.get("permisos_modulos")
            if isinstance(permisos_modulos, list):
                permisos_modulos = ",".join(permisos_modulos)

            sql = """
                UPDATE tb_personal 
                SET nombre = %s, usuario = %s, rol = %s, permisos_modulos = %s, status = %s,
                    idBiometrico = %s, es_servicio_social = %s, horas_objetivo = %s
            """
            params = [
                data.get("nombre"),
                usuario,
                data.get("rol"),
                permisos_modulos,
                data.get("status"),
                id_bio,
                data.get("es_servicio_social", 0),
                data.get("horas_objetivo")
            ]

            if data.get("password"):
                sql += ", password = %s"
                params.append(data.get("password"))
            
            sql += " WHERE idPersonal = %s"
            params.append(id_personal)

            cursor.execute(sql, params)
            conexion.commit()
            return {"success": True}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def delete_personal(id_personal):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM tb_personal WHERE idPersonal = %s", (id_personal,))
            conexion.commit()
            return {"success": True, "mensaje": "Cuenta de personal eliminada correctamente"}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_personal_by_username(usuario):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT idPersonal, nombre, usuario, password, rol, permisos_modulos, status, idBiometrico, es_servicio_social, horas_objetivo
                FROM tb_personal
                WHERE usuario = %s AND status = 'ACTIVO'
                LIMIT 1
            """, (usuario,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()
