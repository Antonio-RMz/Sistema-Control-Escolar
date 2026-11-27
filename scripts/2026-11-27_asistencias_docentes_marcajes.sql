-- =====================================================================================
-- Marcajes del biométrico por día (asistencia de docentes)
-- Fecha: 2026-11-27
--
-- Hasta ahora, al importar el biométrico solo se guardaba por docente y día la primera entrada,
-- la última salida y las horas trabajadas. Los marcajes intermedios se descartaban, así que no se
-- podía saber a qué hora llegó el docente a cada materia.
--
--   marcajes   Horas registradas en el biométrico ese día, en orden y separadas por coma
--              (ej. "11:58,13:00,14:02,15:00,15:58,17:00").
--
-- Con esta columna, en "Análisis de Horas Laboradas" al hacer clic en las horas REALES se ve, por
-- cada clase del día, a qué hora llegó y salió el docente.
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo AGREGA una columna nullable al final de tb_asistencias_docentes. No borra ni modifica datos.
--   * Se puede ejecutar más de una vez: si la columna ya existe no se vuelve a crear.
--   * La API funciona antes y después de ejecutarlo; guarda los marcajes en cuanto existe la columna.
--   * Los días importados antes de ejecutarlo no tienen marcajes: hay que volver a importar el
--     biométrico de esas quincenas para ver el detalle por materia.
-- =====================================================================================

DROP PROCEDURE IF EXISTS agregar_columna_marcajes;
DELIMITER //
CREATE PROCEDURE agregar_columna_marcajes()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_asistencias_docentes' AND COLUMN_NAME = 'marcajes'
    ) THEN
        ALTER TABLE tb_asistencias_docentes ADD COLUMN marcajes VARCHAR(500) NULL DEFAULT NULL;
    END IF;
END //
DELIMITER ;

CALL agregar_columna_marcajes();

DROP PROCEDURE agregar_columna_marcajes;

-- Verificación: debe aparecer la columna marcajes (varchar(500), NULL)
SHOW COLUMNS FROM tb_asistencias_docentes LIKE 'marcajes';
