from flask import Flask, jsonify, request
import pymysql
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def get_connection():
    return pymysql.connect(
        host="localhost", user="root", passwd="root", db="escuelaBTI", charset="utf8mb4"
    )


@app.route("/importar-alumnos-hoja", methods=["POST"])
def importar_alumnos_hoja1():
    try:
        archivo = "GENERACIONES BTI 2026-2018.xlsx"  # ruta del archivo Excel
        # id_generacion = 39  # porque vas a importar solo la hoja 1

        # Leer solo la primera hoja del Excel
        df = pd.read_excel(archivo, sheet_name="GEN 03-06")

        # Limpiar nombres de columnas por si tienen espacios
        df.columns = df.columns.str.strip()

        conexion = get_connection()
        cursor = conexion.cursor()

        insertados = 0

        for index, row in df.iterrows():
            nombre = row.get("nombre")
            apPaterno = row.get("apPaterno")
            apMaterno = row.get("apMaterno")
            fechaNacimiento = row.get("fechaNacimiento")
            tutor = row.get("tutor")
            parentesco = row.get("parentesco")
            calle = row.get("calle")
            colonia = row.get("colonia")
            localidad = row.get("localidad")
            municipio = row.get("municipio")
            telefonoTutor = row.get("telefonoTutor")
            celularAlumno = row.get("celularAlumno")
            correoAlumno = row.get("correoAlumno")
            escuelaProcedencia = row.get("escuelaProcedencia")
            observaciones = row.get("observaciones")
            numeroControl = row.get("numeroControl")

            # Saltar filas vacías
            if (
                pd.isna(nombre)
                and pd.isna(apPaterno)
                and pd.isna(apMaterno)
                and pd.isna(fechaNacimiento)
                and pd.isna(tutor)
                and pd.isna(parentesco)
                and pd.isna(calle)
                and pd.isna(colonia)
                and pd.isna(localidad)
                and pd.isna(municipio)
                and pd.isna(telefonoTutor)
                and pd.isna(celularAlumno)
                and pd.isna(correoAlumno)
                and pd.isna(escuelaProcedencia)
                and pd.isna(observaciones)
                and pd.isna(numeroControl)
            ):
                continue

            query = """
            INSERT INTO tb_alumnos (
                nombre,
                apPaterno,
                apMaterno,
                idGeneracion,
                fechaNacimiento,
                tutor,
                parentesco,
                calle,
                colonia,
                localidad,
                municipio,
                telefonoTutor,
                celularAlumno,
                correoAlumno,
                escuelaProcedencia,
                observaciones,
                numeroControl
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    None if pd.isna(nombre) else str(nombre).strip(),
                    None if pd.isna(apPaterno) else str(apPaterno).strip(),
                    None if pd.isna(apMaterno) else str(apMaterno).strip(),
                    None if pd.isna(fechaNacimiento) else str(fechaNacimiento).strip(),
                    None if pd.isna(tutor) else str(tutor).strip(),
                    None if pd.isna(parentesco) else str(parentesco).strip(),
                    None if pd.isna(calle) else str(calle).strip(),
                    None if pd.isna(colonia) else str(colonia).strip(),
                    None if pd.isna(localidad) else str(localidad).strip(),
                    None if pd.isna(municipio) else str(municipio).strip(),
                    None if pd.isna(telefonoTutor) else str(telefonoTutor).strip(),
                    None if pd.isna(celularAlumno) else str(celularAlumno).strip(),
                    None if pd.isna(correoAlumno) else str(correoAlumno).strip(),
                    (
                        None
                        if pd.isna(escuelaProcedencia)
                        else str(escuelaProcedencia).strip()
                    ),
                    None if pd.isna(observaciones) else str(observaciones).strip(),
                    None if pd.isna(numeroControl) else str(numeroControl).strip(),
                ),
            )

            insertados += 1

        conexion.commit()
        cursor.close()
        conexion.close()

        return (
            jsonify(
                {
                    "mensaje": "Alumnos importados correctamente",
                    "total_insertados": insertados,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


print("ENTRANDO A IMPORTAR")
if __name__ == "__main__":
    app.run(debug=True)
