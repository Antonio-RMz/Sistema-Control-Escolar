-- =====================================================================================
-- Prórroga por periodo (BTI)
-- Fecha: 2026-11-26
--
-- Agrega tb_docente_permisos_captura.periodo: a qué periodo se extiende la prórroga
-- (p1, p2, p3, semestral o extraordinario). En BTI la prórroga solo abre ese periodo para el
-- docente en esa asignatura, hasta su fecha límite, aunque el periodo esté cerrado en el grupo.
-- NULL = prórroga anterior a este cambio (o BGNE): aplica como antes, a todos los periodos.
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo agrega una columna que admite NULL; no modifica datos existentes.
--   * Se puede ejecutar más de una vez: si la columna ya existe no hace nada.
--   * La API funciona antes y después; antes de ejecutarlo, la prórroga BTI no pide periodo.
-- =====================================================================================

SET @tiene_columna := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_docente_permisos_captura' AND COLUMN_NAME = 'periodo'
);

SET @ddl := IF(@tiene_columna > 0,
    'SELECT ''La columna periodo ya existe: no se hizo nada'' AS aviso',
    'ALTER TABLE tb_docente_permisos_captura
        ADD COLUMN periodo VARCHAR(20) NULL DEFAULT NULL
        COMMENT ''Periodo de la prórroga (BTI): p1, p2, p3, semestral o extraordinario; NULL = todos'''
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificación
SHOW COLUMNS FROM tb_docente_permisos_captura LIKE 'periodo';
