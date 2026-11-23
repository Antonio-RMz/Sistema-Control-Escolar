"""
Cliente de los web services REST de Moodle.

Configuración (.env de la API):
    MOODLE_URL    URL base de Moodle (https://moodle.ejemplo.com) o el endpoint completo .../webservice/rest/server.php
    MOODLE_TOKEN  Token del usuario de servicio. Sin token no se llama a Moodle.
    MOODLE_ROLE_ONLINE_ID  (opcional) rol de sistema "Estudiante Online" que se asigna al crear la cuenta.

Funciones de Moodle que debe tener autorizadas el servicio:
    core_user_create_users, core_user_get_users_by_field, core_user_update_users,
    enrol_manual_enrol_users, core_group_get_course_groups, core_group_create_groups,
    core_group_add_group_members, core_role_assign_roles (solo si se usa MOODLE_ROLE_ONLINE_ID)
"""
import json
import logging
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("api")

ROL_ESTUDIANTE = 5
_RUTA_REST = "/webservice/rest/server.php"


def _endpoint():
    url = (os.getenv("MOODLE_URL") or "").strip().rstrip("/")
    if not url:
        return ""
    return url if url.endswith(_RUTA_REST) else url + _RUTA_REST


def nombre_grupo_semana(semana):
    return f"Semana_{int(semana)}"


class MoodleService:
    @staticmethod
    def configurado():
        return bool(_endpoint() and (os.getenv("MOODLE_TOKEN") or "").strip())

    @staticmethod
    def _call(wsfunction, params=None):
        """Llama a un web service. Regresa (ok, datos | mensaje_de_error)."""
        if not MoodleService.configurado():
            return False, "Moodle no está configurado (MOODLE_URL / MOODLE_TOKEN)."
        payload = {"wstoken": os.getenv("MOODLE_TOKEN").strip(), "wsfunction": wsfunction, "moodlewsrestformat": "json"}
        payload.update(params or {})
        req = urllib.request.Request(_endpoint(), data=urllib.parse.urlencode(payload).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                cuerpo = resp.read().decode("utf-8")
            datos = json.loads(cuerpo) if cuerpo.strip() else None
        except Exception as e:
            log.warning("Moodle %s sin respuesta: %s", wsfunction, e)
            return False, f"Sin conexión con Moodle ({wsfunction})."
        if isinstance(datos, dict) and datos.get("exception"):
            log.warning("Moodle %s error: %s", wsfunction, datos)
            return False, f"{wsfunction}: {datos.get('message') or datos.get('errorcode')}"
        return True, datos

    # ------------------------------------------------------------ usuarios

    @staticmethod
    def buscar_usuario(username):
        ok, datos = MoodleService._call("core_user_get_users_by_field", {"field": "username", "values[0]": username})
        if ok and isinstance(datos, list) and datos:
            return datos[0]
        return None

    @staticmethod
    def crear_usuario(username, password, firstname, lastname, email=None):
        """Crea la cuenta o, si ya existe, regresa la existente. {'success', 'moodle_user_id', 'is_new', 'error'}"""
        username = username.lower().strip()
        existente = MoodleService.buscar_usuario(username)
        if existente:
            return {"success": True, "moodle_user_id": existente["id"], "username": username, "is_new": False}

        correo = (email or "").strip().lower() or f"{username}@btinteramericano.edu.mx"
        ok, datos = MoodleService._call("core_user_create_users", {
            "users[0][username]": username,
            "users[0][password]": password,
            "users[0][firstname]": (firstname or "Alumno").strip(),
            "users[0][lastname]": (lastname or "Online").strip(),
            "users[0][email]": correo,
            "users[0][auth]": "manual",
            "users[0][lang]": "es_mx",
        })
        if ok and isinstance(datos, list) and datos and "id" in datos[0]:
            MoodleService.asignar_rol_online(datos[0]["id"])
            return {"success": True, "moodle_user_id": datos[0]["id"], "username": username, "is_new": True}
        return {"success": False, "moodle_user_id": None, "username": username, "error": datos if not ok else "Moodle no regresó el ID del usuario."}

    @staticmethod
    def asignar_rol_online(moodle_user_id):
        rol = (os.getenv("MOODLE_ROLE_ONLINE_ID") or "").strip()
        if not rol.isdigit():
            return True, None
        return MoodleService._call("core_role_assign_roles", {
            "assignments[0][roleid]": int(rol), "assignments[0][userid]": moodle_user_id, "assignments[0][contextid]": 1,
        })

    @staticmethod
    def suspender_usuario(moodle_user_id, suspender=True):
        return MoodleService._call("core_user_update_users", {
            "users[0][id]": moodle_user_id, "users[0][suspended]": 1 if suspender else 0,
        })

    # ------------------------------------------------------------ cursos y grupos

    @staticmethod
    def matricular_en_curso(moodle_user_id, course_id, role_id=ROL_ESTUDIANTE):
        """Matriculación manual (si ya está matriculado, Moodle no hace nada). Regresa (ok, error)."""
        if not moodle_user_id or not course_id:
            return False, "Falta el usuario o el curso de Moodle."
        ok, datos = MoodleService._call("enrol_manual_enrol_users", {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": moodle_user_id,
            "enrolments[0][courseid]": course_id,
        })
        return ok, (None if ok else datos)

    @staticmethod
    def grupos_del_curso(course_id):
        ok, datos = MoodleService._call("core_group_get_course_groups", {"courseid": course_id})
        if not ok:
            return False, datos
        return True, {g.get("name"): g.get("id") for g in (datos or []) if isinstance(g, dict)}

    @staticmethod
    def asegurar_grupos_semana(course_id, hasta_semana, existentes=None):
        """Crea los grupos Semana_1..Semana_N que falten. Regresa (ok, {nombre: id} | error)."""
        if existentes is None:
            ok, existentes = MoodleService.grupos_del_curso(course_id)
            if not ok:
                return False, existentes
        grupos = dict(existentes)
        for s in range(1, int(hasta_semana) + 1):
            nombre = nombre_grupo_semana(s)
            if nombre in grupos:
                continue
            ok, datos = MoodleService._call("core_group_create_groups", {
                "groups[0][courseid]": course_id,
                "groups[0][name]": nombre,
                "groups[0][description]": f"Alumnos online con la semana {s} del bloque pagada.",
            })
            if not ok or not (isinstance(datos, list) and datos and "id" in datos[0]):
                return False, datos if not ok else f"No se pudo crear el grupo {nombre}."
            grupos[nombre] = datos[0]["id"]
        return True, grupos

    @staticmethod
    def habilitar_semana_en_curso(moodle_user_id, course_id, semana_bloque):
        """
        Matricula al alumno en el curso y lo agrega a los grupos Semana_1..Semana_N (acumulativo),
        así ve cada sección semanal restringida por grupo hasta la semana N. Regresa (ok, error).
        """
        ok, err = MoodleService.matricular_en_curso(moodle_user_id, course_id)
        if not ok:
            return False, err
        ok, grupos = MoodleService.asegurar_grupos_semana(course_id, semana_bloque)
        if not ok:
            return False, grupos
        params = {}
        for i, s in enumerate(range(1, int(semana_bloque) + 1)):
            params[f"members[{i}][groupid]"] = grupos[nombre_grupo_semana(s)]
            params[f"members[{i}][userid]"] = moodle_user_id
        ok, datos = MoodleService._call("core_group_add_group_members", params)
        return ok, (None if ok else datos)
