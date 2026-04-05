from flask import Flask, jsonify, request
import pymysql
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        passwd='root',
        db='escuelaBTI',
        charset='utf8mb4'
    )

@app.route('/importar-alumnos-hoja1', methods=['POST'])
def importar_alumnos_hoja1():
    try:
        archivo = 'GENERACIONES43.xlsx'  # ruta del archivo Excel
        id_generacion = 2       # porque vas a importar solo la hoja 1

        # Leer solo la primera hoja del Excel
        df = pd.read_excel(archivo, sheet_name=1)

        # Limpiar nombres de columnas por si tienen espacios
        df.columns = df.columns.str.strip()

        conexion = get_connection()
        cursor = conexion.cursor()

        insertados = 0

        for index, row in df.iterrows():
            nombre = row.get('nombre')
            apPaterno = row.get('apPaterno')
            apMaterno = row.get('apMaterno')

            # Saltar filas vacías
            if pd.isna(nombre) and pd.isna(apPaterno) and pd.isna(apMaterno):
                continue

            query = """
            INSERT INTO tb_alumnos (
                nombre,
                apPaterno,
                apMaterno,
                idGeneracion
            )
            VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (
                None if pd.isna(nombre) else str(nombre).strip(),
                None if pd.isna(apPaterno) else str(apPaterno).strip(),
                None if pd.isna(apMaterno) else str(apMaterno).strip(),
                id_generacion
            ))

            insertados += 1

        conexion.commit()
        cursor.close()
        conexion.close()

        return jsonify({
            "mensaje": "Alumnos importados correctamente",
            "total_insertados": insertados
        }), 201

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)