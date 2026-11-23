-- =====================================================================================
-- Días especiales del calendario de un grupo (pase de lista)
-- Fecha: 2026-11-23
--
-- Tipos:
--   INHABIL     Día feriado o inhábil: no cuenta como día de clase ni como falta.
--   SUSPENSION  Suspensión de clases: no cuenta como día de clase ni como falta; el motivo es obligatorio.
--   EN_LINEA    La clase se dio en línea: sí cuenta como día de clase y se pasa lista normal.
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo CREA una tabla nueva si no existe. No borra, no modifica ni migra datos.
--   * Se puede ejecutar más de una vez sin efecto (IF NOT EXISTS).
--   * tb_asistencias_alumnos y demás tablas NO se tocan: los pases de lista que ya existan
--     en un día marcado como inhábil o suspensión se conservan, solo dejan de contarse.
--
-- La API también crea esta tabla automáticamente la primera vez que se usa.
-- =====================================================================================

CREATE TABLE IF NOT EXISTS tb_grupo_dias_especiales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo INT NOT NULL,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    motivo VARCHAR(255) NULL,
    registrado_por VARCHAR(120) NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_grupo_fecha (id_grupo, fecha),
    KEY idx_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verificación: debe listar la tabla y 0 filas la primera vez
SELECT COUNT(*) AS filas_tb_grupo_dias_especiales FROM tb_grupo_dias_especiales;
