-- =====================================================================================
-- Pase de lista general y pase del docente como registros separados
-- Fecha: 2026-11-26
-- Requiere: scripts/2026-11-23_asistencias_origen_pase.sql (columna es_pase_general)
--
-- Antes la llave única era (id_alumno, id_grupo, id_materia, fecha): el pase general (que escribe
-- una fila por cada materia del horario) y el pase del docente (su materia) compartían la misma
-- fila y se sobrescribían entre sí.
--
-- Ahora la llave incluye es_pase_general, así conviven:
--   es_pase_general = 1  pase general (el que manda: boleta BTI, matriz general, dashboard)
--   es_pase_general = 0  pase del docente (quién estuvo en cada clase; no cambia la boleta)
--   es_pase_general NULL filas anteriores (origen desconocido)
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * No borra ni modifica datos; solo cambia la llave única (la nueva es más amplia que la
--     anterior, así que los datos actuales la cumplen).
--   * Se puede ejecutar más de una vez: si la llave ya incluye es_pase_general no hace nada.
--   * La API funciona antes y después de ejecutarlo; antes, los dos pases se siguen pisando.
--   * Lo que el pase general ya sobrescribió antes de este script no se puede recuperar.
-- =====================================================================================

SET @tiene_columna := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_asistencias_alumnos' AND COLUMN_NAME = 'es_pase_general'
);
SET @llave_nueva := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tb_asistencias_alumnos'
      AND INDEX_NAME = 'uq_alumno_grupo_materia_fecha' AND COLUMN_NAME = 'es_pase_general'
);

SET @ddl := CASE
    WHEN @tiene_columna = 0 THEN
        'SELECT ''Falta es_pase_general: ejecuta antes 2026-11-23_asistencias_origen_pase.sql'' AS aviso'
    WHEN @llave_nueva > 0 THEN
        'SELECT ''La llave ya incluye es_pase_general: no se hizo nada'' AS aviso'
    ELSE
        'ALTER TABLE tb_asistencias_alumnos
            DROP INDEX uq_alumno_grupo_materia_fecha,
            ADD UNIQUE KEY uq_alumno_grupo_materia_fecha (id_alumno, id_grupo, id_materia, fecha, es_pase_general)'
END;

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificación: la llave debe listar id_alumno, id_grupo, id_materia, fecha, es_pase_general
SHOW INDEX FROM tb_asistencias_alumnos WHERE Key_name = 'uq_alumno_grupo_materia_fecha';
