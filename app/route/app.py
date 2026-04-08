from flask import Flask, jsonify, request # Trae Flask (para el servidor) y jsonify (para enviar datos como JSON)
import pymysql                    # Trae la librería para conectar Python con bases de datos MySQL
from flask_cors import CORS
# Crea la aplicación Flask. Es el "cerebro" que manejará las rutas de tu sitio web
app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False
CORS(app)
# Función que sirve como "puerta" para entrar a la base de datos cada vez que la necesites
def get_connection():
    return pymysql.connect(
        host='localhost',         # Dónde está la base de datos (en tu propia compu)
        user='root',              # Usuario de la base de datos
        passwd='root',            # Contraseña de la base de datos
        db='escuelaBTI' ,   
        cursorclass=pymysql.cursors.DictCursor
    )
# Define una "ruta". Cuando alguien entre a http://localhost:5000/alumnos, se activa esta función
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # Parámetros de paginación
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))

        if page < 1:
            page = 1
        if limit < 1:
            limit = 50
        if limit > 200:
            limit = 200

        offset = (page - 1) * limit

        # Filtros opcionales
        idGeneracion = request.args.get('idGeneracion')
        idGrupo = request.args.get('idGrupo')
        search = request.args.get('search', '').strip()

        where = []
        valores = []

        if idGeneracion:
            where.append("idGeneracion = %s")
            valores.append(idGeneracion)

        if idGrupo:
            where.append("idGrupo = %s")
            valores.append(idGrupo)

        # Búsqueda flexible
        if search:
            palabras = search.split()

            for palabra in palabras:
                where.append("""
                    (
                        nombre LIKE %s OR
                        apPaterno LIKE %s OR
                        apMaterno LIKE %s
                    )
                """)
                like = f"%{palabra}%"
                valores.extend([like, like, like])

        where_sql = ""
        if where:
            where_sql = "WHERE " + " AND ".join(where)

        # Total de registros
        sql_total = f"""
            SELECT COUNT(*) AS total
            FROM TB_ALUMNOS
            {where_sql}
        """
        cursor.execute(sql_total, valores)
        total = cursor.fetchone()["total"]

        # Consulta paginada
        sql_datos = f"""
            SELECT 
                idAlumno, nombre, apPaterno, apMaterno, fechaNacimiento,
                tutor, parentesco, calle, colonia, localidad, municipio,
                telefonoTutor, celularAlumno, correoAlumno,
                escuelaProcedencia, observaciones, idGeneracion, idGrupo
            FROM TB_ALUMNOS
            {where_sql}
            ORDER BY idAlumno ASC
            LIMIT %s OFFSET %s
        """

        cursor.execute(sql_datos, valores + [limit, offset])
        alumnos = cursor.fetchall()

        return jsonify({
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "search": search,
            "data": alumnos
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close()     
@app.route('/grupos', methods=['GET'])
def get_grupos():
    
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id, clave, fechaCreacion, fechaInicio, fechaFin
            FROM TB_GRUPOS
        """)

        resultados = cursor.fetchall()
        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close()
@app.route('/generaciones', methods=['GET'])
def get_generaciones():    
    conexion = get_connection()   
    cursor = conexion.cursor()   

    try:
        cursor.execute("""
            SELECT id, nombreGeneracion, mesInicio, mesFin, 
                   anioInicio, aniofin, numeroGeneracion 
            FROM TB_GENERACIONES
        """)

        resultados = cursor.fetchall()

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close()
@app.route('/centroTrabajo', methods=['GET'])
def get_centro_trabajo():      
    conexion = get_connection()   
    cursor = conexion.cursor()   

    try:
        cursor.execute("""
            SELECT id, nombre, direccion, telefono, correo
            FROM TB_CENTROTRABAJO
        """)

        resultados = cursor.fetchall()

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close()
        
@app.route('/tipoPeriodo', methods=['GET'])
def get_tipo_periodo():      
    conexion = get_connection()   
    cursor = conexion.cursor()   

    try:
        cursor.execute("""
            SELECT id,nombrePeriodo, descripcionPeriodo
            FROM TB_TIPOPERIODO
        """)

        resultados = cursor.fetchall()

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close() 
@app.route('/materias', methods=['GET'])
def get_materias():      
    conexion = get_connection()   
    cursor = conexion.cursor()   

    try:
        cursor.execute("""
            SELECT id,nombreMateria, descripcionMateria, idDocente, estatusMateria
            FROM TB_MATERIAS
        """)

        resultados = cursor.fetchall()

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close() 
@app.route('/docentes', methods=['GET'])
def get_docentes():      
    conexion = get_connection()   
    cursor = conexion.cursor()   

    try:
        cursor.execute("""
            SELECT idDocente, nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente
            FROM TB_DOCENTES
        """)

        resultados = cursor.fetchall()

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conexion.close()  
        ## de aqui comienza la seccion POST 
@app.route('/crealumnos', methods=['POST'])
def create_alumno():
    data = request.json

    nombre = data.get('nombre')
    apPaterno = data.get('apPaterno')
    apMaterno = data.get('apMaterno')
    fechaNacimiento = data.get('fechaNacimiento')
    tutor = data.get('tutor')
    parentesco = data.get('parentesco')
    calle = data.get('calle')
    colonia = data.get('colonia')
    localidad = data.get('localidad')
    municipio = data.get('municipio')
    telefonoTutor = data.get('telefonoTutor')
    celularAlumno = data.get('celularAlumno')
    correoAlumno = data.get('correoAlumno')
    escuelaProcedencia = data.get('escuelaProcedencia')
    observaciones = data.get('observaciones')
    idGeneracion = data.get('idGeneracion')
    idGrupo = data.get('idGrupo')
    if not nombre or not apPaterno:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_ALUMNOS (nombre, apPaterno, apMaterno,fechaNacimiento,tutor,parentesco,calle,colonia,localidad,municipio,telefonoTutor,celularAlumno,correoAlumno,escuelaProcedencia,observaciones,idGeneracion,idGrupo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (nombre, apPaterno, apMaterno, fechaNacimiento, tutor, parentesco, calle, colonia, localidad, municipio, telefonoTutor, celularAlumno, correoAlumno, escuelaProcedencia, observaciones, idGeneracion, idGrupo))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Alumno creado correctamente"})
@app.route('/grupos', methods=['POST'])
def create_grupo():
    data = request.json

    clave = data.get('clave')
    fechaCreacion = data.get('fechaCreacion')
    fechaInicio = data.get('fechaInicio')
    fechaFin = data.get('fechaFin')
    id_centroTrabajo = data.get('id_centroTrabajo')
    id_planEstudios = data.get('id_planEstudios')
    id_tipoPeriodo = data.get('id_tipoPeriodo')
    if not clave or not fechaCreacion:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_GRUPOS (clave, fechaCreacion, fechaInicio, fechaFin, id_centroTrabajo, id_tipoPeriodo, id_planEstudios)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (clave, fechaCreacion, fechaInicio, fechaFin, id_centroTrabajo, id_tipoPeriodo, id_planEstudios))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Grupo creado correctamente"})
@app.route('/generaciones', methods=['POST'])
def create_generacion():
    data = request.json

    numeroGeneracion = data.get('numeroGeneracion')
    periodo = data.get('periodo')
    createBy = data.get('createBy')
    UpdateBy = data.get('UpdateBy')
    if not numeroGeneracion or not periodo:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_GENERACIONES (numeroGeneracion, periodo, createBy, UpdateBy)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (numeroGeneracion, periodo, createBy, UpdateBy))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Generación creada correctamente"})

@app.route('/createCentroTrabajo', methods=['POST'])
def create_centro_trabajo():
    data = request.json

    clave = data.get('clave')
    nombre = data.get('nombre')
    direccion = data.get('direccion')
    telefono = data.get('telefono')
    correo = data.get('correo')
    if not clave or not nombre:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_CENTROTRABAJO (clave, nombre, direccion, telefono, correo)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (clave, nombre, direccion, telefono, correo))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Centro de trabajo creado correctamente"})

@app.route('/createTipoPeriodo', methods=['POST'])
def create_tipo_periodo():

    data = request.json

    nombrePeriodo = data.get('nombrePeriodo')
    descripcionPeriodo = data.get('descripcionPeriodo')
    
    if not nombrePeriodo or not descripcionPeriodo:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_TIPOPERIODO (nombrePeriodo, descripcionPeriodo)
    VALUES (%s, %s)
    """

    cursor.execute(query, (nombrePeriodo, descripcionPeriodo))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Tipo de periodo creado correctamente"})

@app.route('/createMateria', methods=['POST'])
def create_materia():
    
    data = request.json

    nombreMateria = data.get('nombreMateria')
    descripcionMateria = data.get('descripcionMateria')
    idDocente = data.get('idDocente')
    estatusMateria = data.get('estatusMateria')
    if not nombreMateria or not idDocente or not estatusMateria:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_MATERIAS (nombreMateria, descripcionMateria, idDocente, estatusMateria)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (nombreMateria, descripcionMateria, idDocente, estatusMateria))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Materia creada correctamente"})
@app.route('/createDocente', methods=['POST'])
def create_docente():
    
    data = request.json

    nombreDocente = data.get('nombreDocente')
    apPaternoDocente = data.get('apPaternoDocente')
    apMaternoDocente = data.get('apMaternoDocente')
    correoDocente = data.get('correoDocente')
    telefonoDocente = data.get('telefonoDocente')
    statusDocente = data.get('statusDocente')
    observacionesDocente = data.get('observacionesDocente')
    if not nombreDocente or not apPaternoDocente or not apMaternoDocente or not correoDocente or not telefonoDocente:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_DOCENTES (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (nombreDocente, apPaternoDocente, apMaternoDocente, correoDocente, telefonoDocente, statusDocente, observacionesDocente))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Docente creado correctamente"})
@app.route('/createPlanEstudios', methods=['POST'])
def create_plan_estudios():
    
    data = request.json

    nombrePlan = data.get('nombrePlan')
    descripcionPlan = data.get('descripcionPlan')
    estatusPlan = data.get('estatusPlan')
    if not nombrePlan or not descripcionPlan or not estatusPlan:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_PLANESESTUDIO (nombrePlan, descripcionPlan, estatusPlan)
    VALUES (%s, %s, %s)
    """

    cursor.execute(query, (nombrePlan, descripcionPlan, estatusPlan))
    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Plan de estudios creado correctamente"})
#ultima seccion 

import os
from flask import send_from_directory

# Ruta al proyecto frontend
FRONTEND_PATH = r'D:\Proyectos\3 test bti'

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Si el archivo existe en la carpeta frontend, lo servimos
    if os.path.exists(os.path.join(FRONTEND_PATH, path)):
        return send_from_directory(FRONTEND_PATH, path)
    # Por defecto, si no existe, devolvemos 404 o podrías redirigir
    return jsonify({"error": "No encontrado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)