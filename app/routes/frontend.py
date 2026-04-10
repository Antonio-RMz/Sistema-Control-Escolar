import os
from flask import Blueprint, send_from_directory, jsonify
from app.config.conexion import FRONTEND_PATH

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def serve_index():
    return send_from_directory(FRONTEND_PATH, 'index.html')

@frontend_bp.route('/<path:path>')
def serve_static(path):
    # Si el archivo existe en la carpeta frontend, lo servimos
    if os.path.exists(os.path.join(FRONTEND_PATH, path)):
        return send_from_directory(FRONTEND_PATH, path)
    # Por defecto, si no existe, devolvemos 404
    return jsonify({"error": "No encontrado"}), 404
