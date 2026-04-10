import pymysql
import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'passwd': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'cursorclass': pymysql.cursors.DictCursor
}

FRONTEND_PATH = os.getenv('FRONTEND_PATH')

def get_connection():
    return pymysql.connect(**DB_CONFIG)