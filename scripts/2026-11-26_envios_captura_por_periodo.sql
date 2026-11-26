-- =====================================================================================
-- Envío de calificaciones por periodo (BTI)
-- Fecha: 2026-11-26
--
-- Cuando el docente envía las calificaciones de un periodo (1er parcial, 2do parcial, semestral…),
-- ese periodo queda bloqueado para él en esa asignatura y grupo: no puede editarlo ni volver a
-- enviarlo. Los demás periodos siguen su propia habilitación (switch + fechas del admin).
-- La administración lo desbloquea al otorgar o actualizar una prórroga (se borran sus envíos).
--
-- SEGURO DE EJECUTAR EN PRODUCCIÓN:
--   * Solo crea una tabla nueva; no toca datos existentes.
--   * Se puede ejecutar más de una vez (CREATE TABLE IF NOT EXISTS).
--   * La API funciona antes y después; antes de ejecutarlo, el envío de un parcial no bloquea nada.
-- =====================================================================================

CREATE TABLE IF NOT EXISTS tb_docente_envios_captura (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    id_docente   INT         NOT NULL,
    id_grupo     INT         NOT NULL,
    id_materia   INT         NOT NULL,
    periodo      VARCHAR(20) NOT NULL COMMENT 'p1, p2, p3, semestral o extraordinario',
    enviado_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_envio_docente_periodo (id_docente, id_grupo, id_materia, periodo),
    KEY idx_envio_grupo_materia (id_grupo, id_materia)
);

-- Verificación
SHOW CREATE TABLE tb_docente_envios_captura;
