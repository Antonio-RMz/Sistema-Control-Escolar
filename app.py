from flask import Flask
from flask_cors import CORS
from app.routes.alumnos import alumnos_bp
from app.routes.grupos import grupos_bp
from app.routes.generaciones import generaciones_bp
from app.routes.catalogos import catalogos_bp
from app.routes.frontend import frontend_bp


def create_app():
    app = Flask(__name__)

    # Configuración de Flask
    app.json.sort_keys = False
    app.json.ensure_ascii = False

    # Habilitar CORS
    CORS(app)

    # Registro de Blueprints
    app.register_blueprint(alumnos_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(generaciones_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(frontend_bp)

    return app


app = create_app()
print(app.url_map)
if __name__ == "__main__":
    print("🔥 EJECUTANDO ESTE APP.PY 🔥")
    # El servidor se ejecuta en el puerto 5000 por defecto
    app.run(host="0.0.0.0", port=5000, debug=True)
