-- Agrega columnas para persistir el desglose del scoring hibrido.
-- Ejecutar en Supabase SQL Editor si la tabla siniestros ya existe.

ALTER TABLE siniestros
  ADD COLUMN IF NOT EXISTS score_reglas INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ml_proba DOUBLE PRECISION DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ml_alerta INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS anom_score_0_1 DOUBLE PRECISION DEFAULT 0,
  ADD COLUMN IF NOT EXISTS explicacion_riesgo TEXT;

ALTER TABLE siniestros
  DROP CONSTRAINT IF EXISTS chk_siniestros_score_reglas,
  DROP CONSTRAINT IF EXISTS chk_siniestros_ml_proba,
  DROP CONSTRAINT IF EXISTS chk_siniestros_ml_alerta,
  DROP CONSTRAINT IF EXISTS chk_siniestros_anom_score;

ALTER TABLE siniestros
  ADD CONSTRAINT chk_siniestros_score_reglas CHECK (score_reglas BETWEEN 0 AND 70),
  ADD CONSTRAINT chk_siniestros_ml_proba CHECK (ml_proba >= 0 AND ml_proba <= 1),
  ADD CONSTRAINT chk_siniestros_ml_alerta CHECK (ml_alerta IN (0, 1)),
  ADD CONSTRAINT chk_siniestros_anom_score CHECK (anom_score_0_1 >= 0 AND anom_score_0_1 <= 1);
