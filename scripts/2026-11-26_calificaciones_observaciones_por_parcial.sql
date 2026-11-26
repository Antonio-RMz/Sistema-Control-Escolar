-- =====================================================================================
-- Observaciones de calificaciones por parcial
-- Fecha: 2026-11-26
--
-- Antes había una sola columna `observaciones` por alumno y materia. Ahora cada etapa de captura
-- tiene la suya; la columna "Observaciones" de la captura muestra y guarda la del parcial habilitado:
--
--   obs_parcial1        1er parcial (BTI) / calificación final (BGNE)
--   obs_parcial2        2do parcial
--   obs_parcial3        3er parcial
--   obs_semestral       examen semestral
--   obs_extraordinario  extraordinario
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo AGREGA columnas nullable al final de tb_calificaciones. No borra ni modifica datos;
--     la columna `observaciones` anterior se conserva tal cual.
--   * Se puede ejecutar más de una vez: las columnas que ya existen no se vuelven a crear.
--   * La API funciona antes y después de ejecutarlo; usa las observaciones por parcial en cuanto
--     existen las columnas (antes sigue con la columna única).
-- =====================================================================================

DROP PROCEDURE IF EXISTS agregar_columna_obs;
DELIMITER //
CREATE PROCEDURE agregar_columna_obs(IN columna VARCHAR(64))
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_calificaciones' AND COLUMN_NAME = columna
    ) THEN
        SET @ddl := CONCAT('ALTER TABLE tb_calificaciones ADD COLUMN ', columna, ' VARCHAR(255) NULL DEFAULT NULL');
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

CALL agregar_columna_obs('obs_parcial1');
CALL agregar_columna_obs('obs_parcial2');
CALL agregar_columna_obs('obs_parcial3');
CALL agregar_columna_obs('obs_semestral');
CALL agregar_columna_obs('obs_extraordinario');

DROP PROCEDURE agregar_columna_obs;

-- Verificación: deben aparecer las 5 columnas obs_* (varchar(255), NULL)
SHOW COLUMNS FROM tb_calificaciones LIKE 'obs\_%';
