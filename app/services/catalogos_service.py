from app.config.conexion import get_connection

class CatalogosService:
    @staticmethod
    def get_centros_trabajo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, nombre, direccion, telefono, correo FROM TB_CENTROTRABAJO")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_centro_trabajo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO TB_CENTROTRABAJO (clave, nombre, direccion, telefono, correo) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (data.get('clave'), data.get('nombre'), data.get('direccion'), data.get('telefono'), data.get('correo')))
            conexion.commit()
            return {"mensaje": "Centro de trabajo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_tipos_periodo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, nombrePeriodo, descripcionPeriodo FROM TB_TIPOPERIODO")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_tipo_periodo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO TB_TIPOPERIODO (nombrePeriodo, descripcionPeriodo) VALUES (%s, %s)"
            cursor.execute(query, (data.get('nombrePeriodo'), data.get('descripcionPeriodo')))
            conexion.commit()
            return {"mensaje": "Tipo de periodo creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_materias():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, nombreMateria, descripcionMateria, idDocente, estatusMateria FROM TB_MATERIAS")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_materia(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO TB_MATERIAS (nombreMateria, descripcionMateria, idDocente, estatusMateria) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (data.get('nombreMateria'), data.get('descripcionMateria'), data.get('idDocente'), data.get('estatusMateria')))
            conexion.commit()
            return {"mensaje": "Materia creada correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_docentes():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente FROM TB_DOCENTES")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_docente(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO TB_DOCENTES (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (data.get('nombreDocente'), data.get('apPaternoDocente'), data.get('apMaternoDocente'), data.get('correoDocente'), data.get('telefonoDocente'), data.get('statusDocente'), data.get('observacionesDocente')))
            conexion.commit()
            return {"mensaje": "Docente creado correctamente"}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_plan_estudios(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO TB_PLANESESTUDIO (nombrePlan, descripcionPlan, estatusPlan) VALUES (%s, %s, %s)"
            cursor.execute(query, (data.get('nombrePlan'), data.get('descripcionPlan'), data.get('estatusPlan')))
            conexion.commit()
            return {"mensaje": "Plan de estudios creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
