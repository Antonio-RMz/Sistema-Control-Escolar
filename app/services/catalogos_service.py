from app.config.conexion import get_connection

class CatalogosService:
    @staticmethod
    def get_centros_trabajo():
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT id, nombre, direccion, telefono, correo FROM tb_centrotrabajo")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_centro_trabajo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_centrotrabajo (clave, nombre, direccion, telefono, correo) VALUES (%s, %s, %s, %s, %s)"
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
            cursor.execute("SELECT id, nombrePeriodo, descripcionPeriodo FROM tb_tipoperiodo")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_tipo_periodo(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_tipoperiodo (nombrePeriodo, descripcionPeriodo) VALUES (%s, %s)"
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
            cursor.execute("SELECT id, nombreMateria, descripcionMateria, idDocente, estatusMateria FROM tb_materias")
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def create_materia(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_materias (nombreMateria, descripcionMateria, idDocente, estatusMateria) VALUES (%s, %s, %s, %s)"
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
            cursor.execute("SELECT idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente FROM tb_docentes")
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
                INSERT INTO tb_docentes (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente)
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
            query = "INSERT INTO tb_planesestudio (nombrePlan, descripcionPlan, estatusPlan) VALUES (%s, %s, %s)"
            cursor.execute(query, (data.get('nombrePlan'), data.get('descripcionPlan'), data.get('estatusPlan')))
            conexion.commit()
            return {"mensaje": "Plan de estudios creado correctamente"}
        finally:
            cursor.close()
            conexion.close()
