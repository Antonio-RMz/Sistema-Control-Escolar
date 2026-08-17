from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from app.routes.alumnos import alumnos_bp
from app.routes.grupos import grupos_bp
from app.routes.generaciones import generaciones_bp
from app.routes.frontend import frontend_bp
from app.routes.asistencias import asistencias_bp
from app.routes.docentes import docentes_bp
from app.routes.materias import materias_bp
from app.routes.planes_estudio import planes_estudio_bp
from app.routes.horarios import horarios_bp
from app.routes.cursos_extra import cursos_extra_bp
from app.routes.centros_trabajo import centros_trabajo_bp
from app.routes.tipos_periodo import tipos_periodo_bp
from app.routes.niveles_academicos import niveles_academicos_bp
from app.routes.calificaciones import calificaciones_bp
from app.routes.notificaciones import notificaciones_bp
from app.routes.personal import personal_bp
from app.routes.permisos_captura import permisos_captura_bp


def create_app():
    app = Flask(__name__)

    # Inicializar Swagger UI
    Swagger(app)

    # Configuración de Flask
    app.json.sort_keys = False
    app.json.ensure_ascii = False

    # Habilitar CORS
    CORS(app)

    # Registro de Blueprints
    app.register_blueprint(alumnos_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(generaciones_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(asistencias_bp)
    app.register_blueprint(docentes_bp)
    app.register_blueprint(materias_bp)
    app.register_blueprint(planes_estudio_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(cursos_extra_bp)
    app.register_blueprint(centros_trabajo_bp)
    app.register_blueprint(tipos_periodo_bp)
    app.register_blueprint(niveles_academicos_bp)
    app.register_blueprint(calificaciones_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(personal_bp)
    app.register_blueprint(permisos_captura_bp)

    # Iniciar programador de tareas diario (7:00 AM)
    from app.utils.scheduler import iniciar_scheduler
    iniciar_scheduler(app)

    return app


app = create_app()
print(app.url_map)
if __name__ == "__main__":
    print("--- EJECUTANDO ESTE APP.PY ---")
    # El servidor se ejecuta en el puerto 5000 por defecto
    app.run(host="0.0.0.0", port=5000, debug=True)
