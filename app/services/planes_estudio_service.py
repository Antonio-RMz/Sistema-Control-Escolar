from app.config.conexion import get_connection
import pymysql


class PlanesEstudioService:
    # Métodos crear planes de estudio
    @staticmethod
    def create_plan_estudios(data):
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            query = "INSERT INTO tb_planesestudio (nombrePlan, descripcionPlan, estatusPlan) VALUES (%s, %s, %s)"
            cursor.execute(
                query,
                (
                    data.get("nombrePlan"),
                    data.get("descripcionPlan"),
                    data.get("estatusPlan"),
                ),
            )
            
            # Obtener el id insertado
            id_plan = cursor.lastrowid
            
            # Recuperar materias enviadas
            materias = data.get("idmaterias", [])
            
            if materias:
                query_rel = "INSERT INTO plan_estudio_materia (idPlanEstudio, idMateria) VALUES (%s, %s)"
                for mat in materias:
                    if isinstance(mat, dict):
                        id_materia = mat.get("idMateria") or mat.get("id")
                    else:
                        id_materia = mat
                        
                    if id_materia:
                        cursor.execute(query_rel, (id_plan, id_materia))

            conexion.commit()
            return {"mensaje": "Plan de estudios creado correctamente", "idPlanEstudio": id_plan}
        except Exception as e:
            conexion.rollback()
            return {"error": str(e)}
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def get_planes_estudio():
        conexion = get_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("""
                SELECT 
                    p.id,
                    p.nombrePlan, 
                    p.descripcionPlan, 
                    p.estatusPlan,
                    IFNULL(GROUP_CONCAT(DISTINCT pm.idMateria), '') AS idmaterias
                FROM tb_planesestudio p
                LEFT JOIN plan_estudio_materia pm ON p.id = pm.idPlanEstudio
                GROUP BY p.id
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                materias_str = row["idmaterias"]
                materias = []
                if materias_str:
                    for m in materias_str.split(","):
                        materias.append(int(m))
                row["idmaterias"] = materias
                
            return rows
        finally:
            cursor.close()
            conexion.close()
