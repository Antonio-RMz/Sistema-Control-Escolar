from flask import Flask, jsonify, request
import pymysql
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        passwd='root',
        db='escuelaBTI',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/generaciones', methods=['POST'])
def create_generacion():
    try:
        data = request.get_json()

        nombreGeneracion = data.get('nombreGeneracion')
        mesInicio = data.get('mesInicio')
        mesFin = data.get('mesFin')
        anioInicio = data.get('anioInicio')
        aniofin = data.get('aniofin')
        numeroGeneracion = data.get('numeroGeneracion')

        mesInicio = mesInicio.upper()
        mesFin = mesFin.upper()

        if mesInicio not in ["FEBRERO", "AGOSTO"]:
            return jsonify({"error": "mesInicio solo puede ser FEBRERO o AGOSTO"}), 400

        if mesFin not in ["AGOSTO", "JULIO", "FEBRERO"]:
            return jsonify({"error": "mesFin solo puede ser AGOSTO, JULIO o FEBRERO"}), 400

        conexion = get_connection()
        cursor = conexion.cursor()

        query = """
        INSERT INTO tb_generaciones
        (nombreGeneracion, mesInicio, mesFin, anioInicio, aniofin, numeroGeneracion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            nombreGeneracion,
            mesInicio,
            mesFin,
            anioInicio,
            aniofin,
            numeroGeneracion
    
        ))

        conexion.commit()

        return jsonify({"mensaje": "Generación creada correctamente"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            cursor.close()
            conexion.close()
        except:
            pass

if __name__ == '__main__':
  
    app.run(host='0.0.0.0', port=5000, debug=True)