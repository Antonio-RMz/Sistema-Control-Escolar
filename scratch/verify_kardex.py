import sys
from app.config.conexion import get_connection
from app.services.calificaciones_service import CalificacionesService
import pymysql

def verify_kardex_reorganization():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    temp_materia_id = None
    temp_calif_id = None
    
    try:
        # 1. Create a duplicate Geografía materia in level 5 (canonical is level 1)
        print("Inserting temporary duplicate materia 'GEOGRAFÍA' in 5th Trimestre (Level 5)...")
        cursor.execute("""
            INSERT INTO tb_materias (nombreMateria, idCentroTrabajo, id_nivel_academico, clave, estatusMateria)
            VALUES ('GEOGRAFÍA', 3, 5, 'TEMP-GEO-5', 'ACTIVA')
        """)
        temp_materia_id = cursor.lastrowid
        print(f"Created temporary materia with ID: {temp_materia_id}")
        
        # 2. Insert a qualification for student 6 in this temporary level 5 Geografía
        print("Inserting temporary grade for student 6 on the duplicate Geografía...")
        cursor.execute("""
            INSERT INTO tb_calificaciones (idAlumno, idMateria, id_nivel_academico, calificacion, tipoAcreditacion, fechaEvaluacion, createBy)
            VALUES (6, %s, 5, 9.5, 'ORDINARIO', CURRENT_DATE, 'VERIFICATION_TEST')
        """, (temp_materia_id,))
        temp_calif_id = cursor.lastrowid
        print(f"Created temporary calificacion with ID: {temp_calif_id}")
        conn.commit()
        
        # 3. Call get_kardex_alumno
        print("\nCalling CalificacionesService.get_kardex_alumno(6)...")
        result = CalificacionesService.get_kardex_alumno(6)
        
        if "error" in result:
            print(f"FAILED: get_kardex_alumno returned error: {result['error']}")
            return
            
        periodos = result["periodos"]
        
        # Let's inspect the results
        geo_in_level_1 = None
        geo_in_level_5 = None
        
        for p in periodos:
            lvl_num = int(p["numeroPeriodo"])
            for m in p["materias"]:
                if m["nombreMateria"] == "GEOGRAFÍA":
                    if lvl_num == 1:
                        geo_in_level_1 = m
                    elif lvl_num == 5:
                        geo_in_level_5 = m
                        
        print("\n--- RESULTS ---")
        if geo_in_level_5:
            print(f"FAIL: Geografía was found in level 5: {geo_in_level_5}")
        else:
            print("PASS: Geografía was NOT found in level 5 (correctly filtered out).")
            
        if geo_in_level_1:
            print(f"PASS: Geografía found in level 1 (correctly mapped).")
            print(f"      Grade in level 1: {geo_in_level_1['calificacion']} (Expected: 9.5)")
            if geo_in_level_1['calificacion'] == 9.5:
                print("PASS: Grade correctly merged into canonical subject!")
            else:
                print("FAIL: Grade was not merged correctly.")
        else:
            print("FAIL: Geografía not found in level 1.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        
    finally:
        print("\nCleaning up temporary records...")
        if temp_calif_id:
            cursor.execute("DELETE FROM tb_calificaciones WHERE id = %s", (temp_calif_id,))
            print(f"Deleted calificacion ID: {temp_calif_id}")
        if temp_materia_id:
            cursor.execute("DELETE FROM tb_materias WHERE id = %s", (temp_materia_id,))
            print(f"Deleted materia ID: {temp_materia_id}")
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_kardex_reorganization()
