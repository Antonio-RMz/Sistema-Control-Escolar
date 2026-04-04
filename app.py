from flask import Flask, jsonify, request # Trae Flask (para el servidor) y jsonify (para enviar datos como JSON)
import pymysql                    # Trae la librería para conectar Python con bases de datos MySQL
from flask_cors import CORS
# Crea la aplicación Flask. Es el "cerebro" que manejará las rutas de tu sitio web
app = Flask(__name__)
CORS(app)
# Función que sirve como "puerta" para entrar a la base de datos cada vez que la necesites
def get_connection():
    return pymysql.connect(
        host='localhost',         # Dónde está la base de datos (en tu propia compu)
        user='root',              # Usuario de la base de datos
        passwd='root',            # Contraseña de la base de datos
        db='escuelaBTI'           # El nombre de la base de datos que quieres usar
    )

# Define una "ruta". Cuando alguien entre a http://localhost:5000/alumnos, se activa esta función
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    conexion = get_connection()   # Llama a la función de arriba para abrir la conexión
    cursor = conexion.cursor()    # Crea un "cursor", que es como el mensajero que lleva y trae datos

    # El mensajero ejecuta la orden SQL para pedir los datos de la tabla de alumnos
    cursor.execute("""
        SELECT id, nombre, apPaterno, apMaterno,id_generacion,id_grupo
        FROM TB_ALUMNOS 
    """)

    # fetchall() atrapa TODOS los registros que encontró la consulta y los guarda en una lista
    resultados = cursor.fetchall()

    # Estas líneas sirven para que tú veas en la consola negra cuántos datos llegaron (para debug)
    print("Cantidad de filas:", len(resultados))
    print("Resultados:", resultados)

    alumnos = []  # Crea una lista vacía de Python para guardar los datos ya limpios

    # Este ciclo recorre cada fila de la base de datos para darle un formato bonito de diccionario
    for fila in resultados:
        alumno = {
            "id": fila[0],         # El primer dato de la fila es el ID
            "nombre": fila[1],     # El segundo es el nombre
            "apPaterno": fila[2],  # El tercero el apellido paterno
            "apMaterno": fila[3],   # El cuarto el apellido materno
            "id_Generacion": fila[4],   # El quinto es el ID de generación
            "id_Grupo": fila[5]    # El sexto es el ID de grupo
        }
        alumnos.append(alumno)     # Agrega ese alumno a nuestra lista general

    conexion.close()               # Cierra la puerta de la base de datos (es buena práctica)

    # Convierte la lista de diccionarios a un formato JSON que el navegador entienda
    return jsonify(alumnos)


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

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    data = request.json

    nombre = data.get('nombre')
    apPaterno = data.get('apPaterno')
    apMaterno = data.get('apMaterno')
    fechaNacimiento = data.get('fechaNacimiento')
    id_generacion = data.get('id_generacion')
    id_grupo = data.get('id_grupo')
    if not nombre or not apPaterno:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = get_connection()
    cursor = conexion.cursor()

    query = """
    INSERT INTO TB_ALUMNOS (nombre, apPaterno, apMaterno,fechaNacimiento,id_generacion,id_grupo)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (nombre, apPaterno, apMaterno, fechaNacimiento, id_generacion, id_grupo))
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
    
    app.run(debug=True)