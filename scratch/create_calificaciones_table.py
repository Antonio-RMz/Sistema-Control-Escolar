from app.config.conexion import get_connection

def run_migration():
    con = get_connection()
    cur = con.cursor()
    try:
        # 1. Agregar id_nivel_academico a tb_materias
        cur.execute("SHOW COLUMNS FROM tb_materias LIKE 'id_nivel_academico'")
        if not cur.fetchone():
            cur.execute("""
                ALTER TABLE tb_materias 
                ADD COLUMN id_nivel_academico INT NULL AFTER idCentroTrabajo,
                ADD CONSTRAINT fk_materias_nivel FOREIGN KEY (id_nivel_academico) REFERENCES tb_niveles_academicos(id) ON DELETE SET NULL
            """)
            print("Columna id_nivel_academico agregada a tb_materias")
        else:
            print("Columna id_nivel_academico ya existía en tb_materias")

        # 2. Crear tabla tb_calificaciones
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_calificaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                idAlumno INT NOT NULL,
                idMateria INT NOT NULL,
                id_nivel_academico INT NULL,
                idGrupo INT NULL,
                calificacion DECIMAL(4,2) NOT NULL DEFAULT 0.00,
                tipoAcreditacion ENUM('ORDINARIO', 'EXTRAORDINARIO', 'EQUIVALENCIA', 'TITULO', 'REGULARIZACION') NOT NULL DEFAULT 'ORDINARIO',
                observaciones VARCHAR(255) NULL,
                fechaEvaluacion DATE NULL,
                createBy VARCHAR(255) NULL,
                createAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                updateBy VARCHAR(255) NULL,
                updateAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_calif_alumno FOREIGN KEY (idAlumno) REFERENCES tb_alumnos(idAlumno) ON DELETE CASCADE,
                CONSTRAINT fk_calif_materia FOREIGN KEY (idMateria) REFERENCES tb_materias(id) ON DELETE CASCADE,
                CONSTRAINT fk_calif_nivel FOREIGN KEY (id_nivel_academico) REFERENCES tb_niveles_academicos(id) ON DELETE SET NULL,
                CONSTRAINT fk_calif_grupo FOREIGN KEY (idGrupo) REFERENCES tb_grupos(id) ON DELETE SET NULL,
                INDEX idx_alumno_nivel (idAlumno, id_nivel_academico)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Tabla tb_calificaciones creada exitosamente")

        con.commit()
    except Exception as e:
        print(f"Error en migración: {e}")
        con.rollback()
    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    run_migration()
