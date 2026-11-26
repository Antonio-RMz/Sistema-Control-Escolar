-- =====================================================================================
-- Origen de cada fila del pase de lista de alumnos (pase general vs. pase por materia)
-- Fecha: 2026-11-23
--
-- Problema: el pase general de Administración guarda una fila por cada materia del horario y
-- el pase por materia (docente) sobrescribe solo la fila de su materia. Si no coinciden (p. ej.
-- A en el pase general y J en una materia), la matriz y la boleta mostraban marcas distintas.
-- Regla de la escuela: el día lo decide el PASE GENERAL.
--
--   es_pase_general = 1  fila escrita por el pase general
--   es_pase_general = 0  fila escrita por un pase por materia
--   es_pase_general NULL fila anterior a este script (origen desconocido): para esos días la
--                        API toma el estatus que tiene la mayoría de las materias.
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo AGREGA una columna nullable al final de la tabla (ALGORITHM=INSTANT en MySQL 8,
--     no reconstruye la tabla). No borra, no modifica ni migra datos.
--   * Se puede ejecutar más de una vez: si la columna ya existe no hace nada.
--   * La API funciona igual antes y después de ejecutarlo; empieza a guardar el origen en
--     cuanto la columna existe.
-- =====================================================================================

SET @existe := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'tb_asistencias_alumnos'
      AND COLUMN_NAME = 'es_pase_general'
);

SET @ddl := IF(@existe = 0,
    'ALTER TABLE tb_asistencias_alumnos ADD COLUMN es_pase_general TINYINT(1) NULL DEFAULT NULL',
    'SELECT ''es_pase_general ya existe: no se hizo nada'' AS aviso');

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificación: debe mostrar la columna es_pase_general (tinyint, NULL)
SHOW COLUMNS FROM tb_asistencias_alumnos LIKE 'es_pase_general';
