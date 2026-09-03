import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.conexion import get_connection

def run_migration():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if colorDocente column exists in tb_docentes
        cursor.execute("SHOW COLUMNS FROM tb_docentes LIKE 'colorDocente'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding column 'colorDocente' to 'tb_docentes'...")
            cursor.execute("ALTER TABLE tb_docentes ADD COLUMN colorDocente VARCHAR(20) DEFAULT '#FFFFFF'")
            conn.commit()
            print("Column 'colorDocente' added successfully!")
        else:
            print("Column 'colorDocente' already exists in 'tb_docentes'.")
            
    except Exception as e:
        conn.rollback()
        print("Error running migration:", e)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
