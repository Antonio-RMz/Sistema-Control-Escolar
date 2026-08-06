import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

def test_endpoint():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        # Test without parameters
        print("Testing GET /horasDocentes with no params:")
        res = client.get("/horasDocentes")
        print("Status:", res.status_code)
        print("Response:", res.get_json())
        print()

        # Test with invalid date format
        print("Testing GET /horasDocentes with invalid date format:")
        res = client.get("/horasDocentes?fecha_inicio=invalid&fecha_fin=2026-08-18")
        print("Status:", res.status_code)
        print("Response:", res.get_json())
        print()

        # Test with valid dates
        print("Testing GET /horasDocentes with valid parameters:")
        res = client.get("/horasDocentes?fecha_inicio=2026-08-16&fecha_fin=2026-08-18")
        print("Status:", res.status_code)
        # Check first element structure
        data = res.get_json()
        print("Status:", res.status_code)
        print("Number of records:", len(data))
        if len(data) > 0:
            print("Sample record structure:", data[0])
        else:
            print("No records found (which is fine if no active teachers exist)")

if __name__ == '__main__':
    test_endpoint()
