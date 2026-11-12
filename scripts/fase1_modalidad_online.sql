-- ==============================================================================
-- FASE 1: MODELO DE DATOS Y ESTRUCTURA PARA MODALIDAD ONLINE
-- Sistema de Control Escolar BTI / BGNE
-- ==============================================================================

-- 1. Agregar columnas para Moodle y asignación de bloques en tb_materias
ALTER TABLE tb_materias 
    ADD COLUMN IF NOT EXISTS id_curso_moodle INT NULL DEFAULT NULL COMMENT 'ID del curso correspondiente en Moodle' AFTER clave,
    ADD COLUMN IF NOT EXISTS mes_bloque TINYINT NULL DEFAULT NULL COMMENT 'Mes o bloque en modalidad online (1, 2, 3)' AFTER id_curso_moodle,
    ADD COLUMN IF NOT EXISTS par_materia_orden TINYINT NULL DEFAULT 1 COMMENT '1 = Primera materia del mes, 2 = Segunda materia del mes' AFTER mes_bloque;

-- 2. Agregar columnas para punto de inicio y acumulado en tb_alumnos
ALTER TABLE tb_alumnos 
    ADD COLUMN IF NOT EXISTS trimestre_inicio_online INT DEFAULT 1 COMMENT 'Trimestre en que inició modalidad online' AFTER semana_actual_pagada,
    ADD COLUMN IF NOT EXISTS semanas_totales_pagadas INT DEFAULT 0 COMMENT 'Total acumulado de semanas pagadas' AFTER trimestre_inicio_online;

-- 3. Agregar columnas de detalle en tb_alumno_pagos
ALTER TABLE tb_alumno_pagos 
    ADD COLUMN IF NOT EXISTS semanas_pagadas INT DEFAULT 1 COMMENT 'Cantidad de semanas pagadas en esta exhibicion' AFTER semana_cubierta,
    ADD COLUMN IF NOT EXISTS id_nivel_academico INT NULL COMMENT 'Trimestre o nivel academico cubierto' AFTER semanas_pagadas,
    ADD COLUMN IF NOT EXISTS mes_bloque INT NULL COMMENT 'Mes cubierto (1, 2, 3)' AFTER id_nivel_academico;

-- 4. Crear tabla de control granular de actividades/semanas por alumno
CREATE TABLE IF NOT EXISTS tb_alumno_actividades_online (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    id_materia INT NOT NULL,
    id_nivel_academico INT NOT NULL,
    mes_bloque TINYINT NOT NULL COMMENT 'Mes del bloque: 1, 2 o 3',
    semana TINYINT NOT NULL COMMENT 'Semana de la materia: 1, 2, 3 o 4',
    id_pago INT NULL COMMENT 'ID del pago que liberó esta semana',
    fecha_liberacion DATETIME NULL COMMENT 'Fecha y hora en que se liberó la semana (al registrar el pago)',
    fecha_entrega DATETIME NULL COMMENT 'Fecha y hora en que el alumno subió la tarea en Moodle',
    estatus ENUM('BLOQUEADA', 'LIBERADA', 'ENTREGADA', 'CALIFICADA') DEFAULT 'BLOQUEADA',
    moodle_submission_id BIGINT NULL COMMENT 'ID de la entrega de la tarea en Moodle',
    calificacion DECIMAL(5,2) NULL COMMENT 'Calificación obtenida en Moodle',
    observaciones VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_alumno_materia_semana (id_alumno, id_materia, semana),
    INDEX idx_alumno_nivel (id_alumno, id_nivel_academico),
    INDEX idx_pago (id_pago),
    CONSTRAINT fk_actividades_alumno FOREIGN KEY (id_alumno) REFERENCES tb_alumnos(idAlumno) ON DELETE CASCADE,
    CONSTRAINT fk_actividades_materia FOREIGN KEY (id_materia) REFERENCES tb_materias(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 5. MAPEO DE MESES Y MATERIAS (BGNE - CCT 3)
-- ==============================================================================

-- --- PRIMER TRIMESTRE ---
-- MES I: Informática I (10) y Geografía (9) / Intro Ciencias Sociales (12)
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 1 WHERE id = 10;
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 2 WHERE id IN (9, 12);
-- MES II: Lectura y Redacción I (13) y Química I (11)
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 1 WHERE id = 13;
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 2 WHERE id = 11;
-- MES III: Matemáticas I (8) e Inglés I (14)
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 1 WHERE id = 8;
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 2 WHERE id = 14;

-- --- SEGUNDO TRIMESTRE ---
-- MES I: Informática II (17) y Lectura y Redacción II (20)
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 1 WHERE id = 17;
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 2 WHERE id = 20;
-- MES II: Biología I (16) / Historia de México I (19) y Química II (18)
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 1 WHERE id IN (16, 19);
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 2 WHERE id = 18;
-- MES III: Matemáticas II (15) e Inglés II (21)
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 1 WHERE id = 15;
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 2 WHERE id = 21;

-- --- TERCER TRIMESTRE ---
-- MES I: Literatura I (27) y Biología II (24)
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 1 WHERE id = 27;
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 2 WHERE id = 24;
-- MES II: Hist. México II (26) / Met. Investigación I (23) y Matemáticas III (22)
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 1 WHERE id IN (26, 23);
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 2 WHERE id = 22;
-- MES III: Inglés III (28) y Física I (25)
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 1 WHERE id = 28;
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 2 WHERE id = 25;

-- --- CUARTO TRIMESTRE ---
-- MES I: Literatura II (34) y Física II (32)
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 1 WHERE id = 34;
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 2 WHERE id = 32;
-- MES II: Estructura Socioec. Méx (33) / Ecología (30) e Inglés IV (35)
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 1 WHERE id IN (33, 30);
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 2 WHERE id = 35;
-- MES III: Met. Investigación II (31) y Matemáticas IV (29)
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 1 WHERE id = 31;
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 2 WHERE id = 29;

-- --- QUINTO TRIMESTRE ---
-- MES I: Informática III (36) y Contabilidad I (40)
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 1 WHERE id = 36;
UPDATE tb_materias SET mes_bloque = 1, par_materia_orden = 2 WHERE id = 40;
-- MES II: Cálculo Diferencial (37) e Individuo y Sociedad (38)
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 1 WHERE id = 37;
UPDATE tb_materias SET mes_bloque = 2, par_materia_orden = 2 WHERE id = 38;
-- MES III: Temas Selectos de Biología I (41) e Inglés V (39)
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 1 WHERE id = 41;
UPDATE tb_materias SET mes_bloque = 3, par_materia_orden = 2 WHERE id = 39;
