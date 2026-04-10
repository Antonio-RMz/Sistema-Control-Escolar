import pymysql
import os

# Configuración de la base de datos
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'api_user',
    'passwd': '123456',
    'db': 'escuelabti',
    'cursorclass': pymysql.cursors.DictCursor
}

# Ruta al proyecto frontend
FRONTEND_PATH = r'D:\Proyectos\3 test bti'

def get_connection():
    """Establece y devuelve una conexión a la base de datos MySQL."""
    return pymysql.connect(**DB_CONFIG)
