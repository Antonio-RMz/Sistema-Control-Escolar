import sys
import os
import io

import importlib.util

# Cargar app.py dinámicamente para evitar conflictos con la carpeta app/
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app_py_path = os.path.join(parent_dir, 'app.py')

sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location("app_module", app_py_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app

def run_test():
    app.testing = True
    with app.test_client() as client:
        # Case A: No file in request
        print("Testing Case A: No file in request...")
        res = client.post("/asistencias/upload")
        print("Status:", res.status_code)
        print("Response:", res.get_json())
        assert res.status_code == 400
        assert "No se envió" in res.get_json()["error"]
        print("Case A PASSED!")
        print()

        # Case B: Invalid file extension (.txt)
        print("Testing Case B: Invalid file extension...")
        data = {
            "file": (io.BytesIO(b"dummy text content"), "test_file.txt")
        }
        res = client.post("/asistencias/upload", data=data, content_type="multipart/form-data")
        print("Status:", res.status_code)
        print("Response:", res.get_json())
        assert res.status_code == 400
        assert "Formato de archivo no permitido" in res.get_json()["error"]
        print("Case B PASSED!")
        print()

        # Case C: Valid Excel file (.xlsx)
        print("Testing Case C: Valid Excel file...")
        # Create a dummy bytes stream simulating an Excel file
        data = {
            "file": (io.BytesIO(b"dummy excel content"), "test_file.xlsx")
        }
        res = client.post("/asistencias/upload", data=data, content_type="multipart/form-data")
        print("Status:", res.status_code)
        resp_json = res.get_json()
        print("Response:", resp_json)
        assert res.status_code == 200
        assert "Archivo recibido" in resp_json["mensaje"]
        
        # Verify file is saved inside uploads
        filename = resp_json["filename"]
        saved_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "uploads", filename)
        assert os.path.exists(saved_path), f"File {saved_path} was not saved!"
        print(f"File verified at: {saved_path}")
        
        # Cleanup saved file
        os.remove(saved_path)
        print("Cleanup completed.")
        print("Case C PASSED!")
        print()

        print("--- ALL UPLOAD TESTS PASSED SUCCESSFULLY! ---")

if __name__ == '__main__':
    run_test()
