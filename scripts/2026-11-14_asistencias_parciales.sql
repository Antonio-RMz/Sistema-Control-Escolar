-- =====================================================================================
-- Asistencias por parcial (BTI) para la boleta de calificaciones
-- Fecha: 2026-11-14
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo CREA una tabla nueva si no existe. No borra, no modifica ni migra datos.
--   * Se puede ejecutar más de una vez sin efecto (IF NOT EXISTS).
--   * tb_calificaciones, tb_asistencias_alumnos y demás tablas NO se tocan.
--
-- La API también crea esta tabla automáticamente la primera vez que se captura una
-- asistencia por parcial; ejecutar este script antes solo lo hace de forma controlada.
-- =====================================================================================

CREATE TABLE IF NOT EXISTS tb_asistencias_parciales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    id_grupo INT NOT NULL,
    id_nivel_academico INT NOT NULL,
    parcial TINYINT NOT NULL,
    total_clases INT NULL,
    asistencias INT NULL,
    updated_by VARCHAR(120) NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_alumno_grupo_nivel_parcial (id_alumno, id_grupo, id_nivel_academico, parcial),
    KEY idx_grupo_nivel (id_grupo, id_nivel_academico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verificación: debe listar la tabla y 0 filas la primera vez
SELECT COUNT(*) AS filas_tb_asistencias_parciales FROM tb_asistencias_parciales;
