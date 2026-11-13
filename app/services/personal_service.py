from app.config.conexion import get_connection
from app.utils.seguridad import (
    auditar, hash_password, usuario_en_uso, validar_password_nueva, verificar_password,
)

# Columnas públicas: NUNCA incluir "password"
_COLUMNAS = """
    idPersonal, nombre, usuario, rol, permisos_modulos, status,
    idBiometrico, es_servicio_social, horas_objetivo, createAt, updateAt
"""


def _permisos_a_texto(permisos):
    """Lista o texto → 'mod:accion,...'. Vacío significa SIN permisos (no se asignan por defecto)."""
    if isinstance(permisos, list):
        permisos = ",".join(p.strip() for p in permisos if p and p.strip())
    return (permisos or "").strip()


class PersonalService:
    @staticmethod
    def get_personales(page, limit, search, status):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            page = max(1, page)
            limit = max(1, min(limit, 500))
            where = " WHERE 1=1"
            params = []
            if search:
                where += " AND (nombre LIKE %s OR usuario LIKE %s OR rol LIKE %s OR idBiometrico LIKE %s)"
                like = f"%{search}%"
                params.extend([like, like, like, like])
            if status:
                where += " AND status = %s"
                params.append(status)

            cursor.execute("SELECT COUNT(*) AS total FROM tb_personal" + where, params)
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"SELECT {_COLUMNAS} FROM tb_personal{where} ORDER BY status = 'ACTIVO' DESC, nombre ASC LIMIT %s OFFSET %s",
                params + [limit, (page - 1) * limit],
            )
            return {
                "data": cursor.fetchall(),
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": max(1, -(-total // limit)),
            }
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def _validar_biometrico(cursor, id_bio, id_personal=None):
        if id_bio is None or str(id_bio).strip() == "":
            return None, None
        id_bio = str(id_bio).strip()
        cursor.execute(
            "SELECT idPersonal, nombre FROM tb_personal WHERE idBiometrico = %s AND (%s IS NULL OR idPersonal != %s)",
            (id_bio, id_personal, id_personal),
        )
        p_dup = cursor.fetchone()
        if p_dup:
            return None, f"El ID Biométrico '{id_bio}' ya está asignado al personal '{p_dup['nombre']}'."
        cursor.execute("SELECT nombreDocente FROM tb_docentes WHERE idBiometrico = %s", (id_bio,))
        d_dup = cursor.fetchone()
        if d_dup:
            return None, f"El ID Biométrico '{id_bio}' ya está asignado al docente '{d_dup['nombreDocente']}'."
        return id_bio, None

    @staticmethod
    def create_personal(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            usuario = (data.get("usuario") or "").strip()
            en_uso = usuario_en_uso(cursor, usuario)
            if en_uso:
                return {"error": f"El nombre de usuario ya está asignado a {en_uso}."}

            error_pw = validar_password_nueva(data.get("password"))
            if error_pw:
                return {"error": error_pw}

            id_bio, error_bio = PersonalService._validar_biometrico(cursor, data.get("idBiometrico"))
            if error_bio:
                return {"error": error_bio}

            permisos = _permisos_a_texto(data.get("permisos_modulos"))
            cursor.execute(
                """
                INSERT INTO tb_personal (nombre, usuario, password, rol, permisos_modulos, status, idBiometrico, es_servicio_social, horas_objetivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data.get("nombre"), usuario, hash_password(data.get("password")), data.get("rol"),
                    permisos, data.get("status", "ACTIVO"), id_bio,
                    data.get("es_servicio_social", 0), data.get("horas_objetivo"),
                ),
            )
            conexion.commit()
            nuevo_id = cursor.lastrowid
            auditar("personal.crear", idPersonal=nuevo_id, cuenta=usuario, rol=data.get("rol"), permisos=permisos)
            return {"success": True, "idPersonal": nuevo_id}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_personal_by_id(id_personal):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(f"SELECT {_COLUMNAS} FROM tb_personal WHERE idPersonal = %s", (id_personal,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def update_personal(id_personal, data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT idPersonal, usuario, status, permisos_modulos FROM tb_personal WHERE idPersonal = %s", (id_personal,))
            actual = cursor.fetchone()
            if not actual:
                return {"error": "Cuenta de personal no encontrada", "_status": 404}

            usuario = (data.get("usuario") or "").strip()
            en_uso = usuario_en_uso(cursor, usuario, excluir_tabla="tb_personal", excluir_id=id_personal)
            if en_uso:
                return {"error": f"El nombre de usuario ya está asignado a {en_uso}."}

            id_bio, error_bio = PersonalService._validar_biometrico(cursor, data.get("idBiometrico"), id_personal)
            if error_bio:
                return {"error": error_bio}

            permisos = _permisos_a_texto(data.get("permisos_modulos"))
            sql = """
                UPDATE tb_personal
                SET nombre = %s, usuario = %s, rol = %s, permisos_modulos = %s, status = %s,
                    idBiometrico = %s, es_servicio_social = %s, horas_objetivo = %s
            """
            params = [
                data.get("nombre"), usuario, data.get("rol"), permisos, data.get("status"),
                id_bio, data.get("es_servicio_social", 0), data.get("horas_objetivo"),
            ]

            cambio_password = bool(data.get("password"))
            if cambio_password:
                error_pw = validar_password_nueva(data.get("password"))
                if error_pw:
                    return {"error": error_pw}
                sql += ", password = %s"
                params.append(hash_password(data.get("password")))

            sql += " WHERE idPersonal = %s"
            params.append(id_personal)
            cursor.execute(sql, params)
            conexion.commit()

            auditar(
                "personal.editar", idPersonal=id_personal, cuenta=usuario,
                status=f"{actual['status']}->{data.get('status')}" if actual["status"] != data.get("status") else data.get("status"),
                permisos_cambiaron=(actual["permisos_modulos"] or "") != permisos,
                password_cambiada=cambio_password,
            )
            return {"success": True}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def desactivar_personal(id_personal):
        """Baja lógica: conserva el historial (asistencias por biométrico, bitácora)."""
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("UPDATE tb_personal SET status = 'INACTIVO' WHERE idPersonal = %s", (id_personal,))
            conexion.commit()
            if cursor.rowcount == 0:
                cursor.execute("SELECT 1 FROM tb_personal WHERE idPersonal = %s", (id_personal,))
                if not cursor.fetchone():
                    return {"error": "Cuenta de personal no encontrada", "_status": 404}
            auditar("personal.desactivar", idPersonal=id_personal)
            return {"success": True, "mensaje": "Cuenta de personal desactivada correctamente"}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_personal_by_username(usuario):
        """Datos públicos de una cuenta activa (sin contraseña)."""
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM tb_personal WHERE usuario = %s AND status = 'ACTIVO' LIMIT 1",
                (usuario,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def login(usuario, password):
        """
        Verifica credenciales dentro de la API: el hash nunca sale del backend.
        Devuelve (estado, datos): estado ∈ {'ok', 'no_existe', 'inactivo', 'sin_password', 'password'}.
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                f"SELECT {_COLUMNAS}, password FROM tb_personal WHERE usuario = %s LIMIT 1",
                ((usuario or "").strip(),),
            )
            fila = cursor.fetchone()
            if not fila:
                return "no_existe", None
            hash_guardado = fila.pop("password", None)
            if fila["status"] != "ACTIVO":
                return "inactivo", None
            if not hash_guardado:
                return "sin_password", None
            if not verificar_password(password, hash_guardado):
                return "password", None
            return "ok", fila
        finally:
            cursor.close()
            conexion.close()
