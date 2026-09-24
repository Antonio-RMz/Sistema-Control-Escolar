import os
import json
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

MOODLE_URL = os.getenv('MOODLE_URL', 'https://moodle.btinteramericano.com/webservice/rest/server.php')
MOODLE_TOKEN = os.getenv('MOODLE_TOKEN', '064140244fcfb5f99535c095e0f2c638')

class MoodleService:
    @staticmethod
    def _call(wsfunction, params=None):
        """Ejecuta una petición a la API WebService REST de Moodle"""
        if params is None:
            params = {}
        
        payload = {
            'wstoken': MOODLE_TOKEN,
            'wsfunction': wsfunction,
            'moodlewsrestformat': 'json'
        }
        payload.update(params)
        
        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(MOODLE_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except Exception as e:
            return {'error': str(e), 'success': False}

    @staticmethod
    def crear_usuario(username, password, firstname, lastname, email=None):
        """
        Crea un nuevo usuario en Moodle (core_user_create_users).
        Si el usuario ya existe o hubo error, busca si ya está registrado para obtener su ID.
        """
        clean_user = username.lower().strip()
        domain = "btinteramericano.edu.mx"
        clean_email = email.strip().lower() if email else f"{clean_user}@{domain}"
        
        params = {
            'users[0][username]': clean_user,
            'users[0][password]': password,
            'users[0][firstname]': firstname.strip() if firstname else 'Alumno',
            'users[0][lastname]': lastname.strip() if lastname else 'Online',
            'users[0][email]': clean_email,
            'users[0][auth]': 'manual'
        }
        res = MoodleService._call('core_user_create_users', params)
        
        # Moodle responde con array: [{'id': 123, 'username': '...'}]
        if isinstance(res, list) and len(res) > 0 and 'id' in res[0]:
            return {
                'success': True,
                'moodle_user_id': res[0]['id'],
                'username': res[0]['username'],
                'password': password,
                'is_new': True
            }
            
        # Si falló o el servicio no tiene la función activa, buscar si ya existe
        search_res = MoodleService._call('core_user_get_users_by_field', {
            'field': 'username',
            'values[0]': clean_user
        })
        if isinstance(search_res, list) and len(search_res) > 0 and 'id' in search_res[0]:
            return {
                'success': True,
                'moodle_user_id': search_res[0]['id'],
                'username': clean_user,
                'password': password,
                'is_new': False
            }
            
        # En caso de que el token no tenga permisos activos de admin en Moodle, generamos las credenciales
        # para que el sistema escolar las guarde y el administrativo no quede bloqueado
        return {
            'success': False,
            'moodle_user_id': None,
            'username': clean_user,
            'password': password,
            'error': res.get('message') if isinstance(res, dict) else str(res),
            'note': 'Credenciales generadas localmente para el alumno.'
        }

    @staticmethod
    def matricular_en_curso(moodle_user_id, course_id, role_id=5):
        """Matricula al usuario con rol de estudiante (roleid=5)"""
        if not moodle_user_id or not course_id:
            return {'success': False, 'message': 'Faltan parámetros de usuario o curso'}
            
        params = {
            'enrolments[0][roleid]': role_id,
            'enrolments[0][userid]': moodle_user_id,
            'enrolments[0][courseid]': course_id
        }
        res = MoodleService._call('enrol_manual_enrol_users', params)
        return {'success': True, 'response': res}

    @staticmethod
    def asegurar_grupo_semana(course_id, semana):
        """Busca o crea el grupo 'Semana {semana} Pagada' en el curso de Moodle"""
        group_name = f"Semana {semana} Pagada"
        groups = MoodleService._call('core_group_get_course_groups', {'courseid': course_id})
        if isinstance(groups, list):
            for g in groups:
                if g.get('name') == group_name:
                    return g.get('id')
                    
        # Crear grupo
        create_res = MoodleService._call('core_group_create_groups', {
            'groups[0][courseid]': course_id,
            'groups[0][name]': group_name,
            'groups[0][description]': f"Acceso a contenidos de la Semana {semana} acreditada."
        })
        if isinstance(create_res, list) and len(create_res) > 0 and 'id' in create_res[0]:
            return create_res[0]['id']
        return None

    @staticmethod
    def desbloquear_semana(moodle_user_id, course_id, semana):
        """
        Asigna al alumno al grupo de la semana pagada y acumulativamente a las semanas anteriores.
        Regla de negocio: Si paga Semana 2, se le asegura acceso a Semana 1 y Semana 2.
        """
        if not moodle_user_id or not course_id:
            return {'success': False, 'message': 'moodle_user_id o course_id no definidos'}
            
        detalles = []
        for s in range(1, semana + 1):
            group_id = MoodleService.asegurar_grupo_semana(course_id, s)
            if group_id:
                res_add = MoodleService._call('core_group_add_group_members', {
                    'members[0][groupid]': group_id,
                    'members[0][userid]': moodle_user_id
                })
                detalles.append({'semana': s, 'group_id': group_id, 'result': res_add})
                
        return {'success': True, 'semanas': detalles}
