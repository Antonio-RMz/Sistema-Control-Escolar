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

    
    cursor.execute("""
        SELECT id, clave, fechaCreacion, fechaInicio, fechaFin 
        FROM TB_GRUPOS
    """)

   
    resultados = cursor.fetchall()

   
    print("Cantidad de filas:", len(resultados))
    print("Resultados:", resultados)

    grupos = []  

    
    for fila in resultados:
        grupo = {
            "id": fila[0],         # El primer dato de la fila es el ID
            "clave": fila[1],      # El segundo es la clave
            "fechaCreacion": fila[2], # El tercero es la fecha de creación
            "fechaInicio": fila[3],  # El cuarto es la fecha de inicio
            "fechaFin": fila[4]   # El quinto es la fecha de fin
        }
        grupos.append(grupo)     # Agrega ese grupo a nuestra lista general

    conexion.close()               # Cierra la puerta de la base de datos (es buena práctica)

    # Convierte la lista de diccionarios a un formato JSON que el navegador entienda
    return jsonify(grupos)

@app.route('/generaciones', methods=['GET'])
def get_generaciones():    
    conexion = get_connection()   
    cursor = conexion.cursor()   

    
    cursor.execute("""
        SELECT id, numeroGeneracion, periodo, createBy, UpdateBy 
        FROM TB_GENERACIONES
    """)

   
    resultados = cursor.fetchall()

   
    print("Cantidad de filas:", len(resultados))
    print("Resultados:", resultados)

    generaciones = []  

    
    for fila in resultados:
        generacion = {
            "id": fila[0],         # El primer dato de la fila es el ID
            "numeroGeneracion": fila[1],      # El segundo es el número de generación
            "periodo": fila[2],  # El tercero es el periodo
            "createBy": fila[3],  # El cuarto es el creador
            "UpdateBy": fila[4]   # El quinto es el actualizador
        }
        generaciones.append(generacion)     # Agrega esa generación a nuestra lista general

    conexion.close()               # Cierra la puerta de la base de datos (es buena práctica)

    # Convierte la lista de diccionarios a un formato JSON que el navegador entienda
    return jsonify(generaciones)

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
    if not clave or not fechaCreacion:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_GRUPOS (clave, fechaCreacion, fechaInicio, fechaFin)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (clave, fechaCreacion, fechaInicio, fechaFin))
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



#ultima seccion 
if __name__ == '__main__':
    
  app.run(host='0.0.0.0', port=5000, debug=True)