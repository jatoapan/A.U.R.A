-- =====================================================================
-- MASTER SCHEMA PARA A.U.R.A (Sistema de Deteccion de Fraude)
-- Hackathon Reto 2.1 e Ingestion Ecuador Nacional
-- Implementacion: pgvector (384D) + HNSW (Supabase recomendado)
-- =====================================================================

-- 0. Limpieza total (Borrado en orden de dependencias)
DROP FUNCTION IF EXISTS buscar_narrativas_similares(vector, float, int);
DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS siniestros;
DROP TABLE IF EXISTS cambios_asegurado;
DROP TABLE IF EXISTS vehiculos;
DROP TABLE IF EXISTS conductores;
DROP TABLE IF EXISTS beneficiarios;
DROP TABLE IF EXISTS intermediarios;
DROP TABLE IF EXISTS proveedores;
DROP TABLE IF EXISTS polizas;
DROP TABLE IF EXISTS asegurados;

-- 1. Habilitar la extension para busqueda vectorial
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. TABLA: ASEGURADOS
CREATE TABLE asegurados (
    id_asegurado VARCHAR(36) PRIMARY KEY,
    nombre_completo TEXT NOT NULL,
    documento_identidad VARCHAR(20) NOT NULL,
    telefono VARCHAR(20),
    correo_electronico TEXT,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    segmento VARCHAR(30),
    antiguedad_meses INT,
    ciudad VARCHAR(50),
    numero_polizas INT,
    reclamos_ultimos_12_meses INT,
    mora_actual BOOLEAN DEFAULT FALSE,
  lista_restrictiva BOOLEAN DEFAULT FALSE,
    CONSTRAINT chk_asegurados_antiguedad_nonneg CHECK (antiguedad_meses IS NULL OR antiguedad_meses >= 0),
    CONSTRAINT chk_asegurados_numero_polizas_nonneg CHECK (numero_polizas IS NULL OR numero_polizas >= 0),
    CONSTRAINT chk_asegurados_reclamos12m_nonneg CHECK (reclamos_ultimos_12_meses IS NULL OR reclamos_ultimos_12_meses >= 0)
);

-- 3. TABLA: POLIZAS
CREATE TABLE polizas (
    id_poliza VARCHAR(36) PRIMARY KEY,
    id_asegurado VARCHAR(36) NOT NULL REFERENCES asegurados(id_asegurado),
    numero_poliza VARCHAR(30) UNIQUE NOT NULL,
    ramo VARCHAR(30) NOT NULL,
    fecha_inicio_vigencia TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_fin_vigencia TIMESTAMP WITH TIME ZONE NOT NULL,
    monto_asegurado NUMERIC(12, 2) NOT NULL,
    suma_asegurada NUMERIC(12, 2),
    prima NUMERIC(10, 2),
    deducible NUMERIC(10, 2),
    canal_venta VARCHAR(40),
    ciudad VARCHAR(50),
    tipo_cobertura VARCHAR(100) NOT NULL,
    estado_poliza VARCHAR(20) DEFAULT 'ACTIVA',
    CONSTRAINT chk_polizas_fechas CHECK (fecha_fin_vigencia >= fecha_inicio_vigencia),
    CONSTRAINT chk_polizas_montos_nonneg CHECK (
      monto_asegurado >= 0
      AND (suma_asegurada IS NULL OR suma_asegurada >= 0)
      AND (prima IS NULL OR prima >= 0)
      AND (deducible IS NULL OR deducible >= 0)
    )
);

-- 4. TABLA: VEHICULOS
CREATE TABLE vehiculos (
    id_vehiculo VARCHAR(36) PRIMARY KEY,
    id_poliza VARCHAR(36) NOT NULL REFERENCES polizas(id_poliza),
    placa VARCHAR(10) NOT NULL,
    chasis VARCHAR(30) NOT NULL,
    motor VARCHAR(30) NOT NULL,
    marca VARCHAR(30),
    modelo VARCHAR(30),
    anio INT,
    CONSTRAINT chk_vehiculos_anio CHECK (anio IS NULL OR (anio >= 1950 AND anio <= 2100))
);

-- 5.1 TABLA: CONDUCTORES
CREATE TABLE conductores (
  id_conductor VARCHAR(36) PRIMARY KEY,
  nombre_completo TEXT NOT NULL,
  documento_identidad VARCHAR(20),
  ciudad VARCHAR(50),
  historial_siniestros INT,
  lista_restrictiva BOOLEAN DEFAULT FALSE,
  CONSTRAINT chk_conductores_historial_nonneg CHECK (historial_siniestros IS NULL OR historial_siniestros >= 0)
);

-- 5. TABLA: PROVEEDORES (Talleres, Peritos, etc.)
CREATE TABLE proveedores (
    id_proveedor VARCHAR(36) PRIMARY KEY,
    nombre_comercial TEXT NOT NULL,
    ruc_cedula VARCHAR(20) NOT NULL,
    tipo_proveedor VARCHAR(50) NOT NULL,
    ciudad VARCHAR(50),
    reclamos_asociados INT,
    monto_promedio_reclamado NUMERIC(12, 2),
    porcentaje_casos_observados NUMERIC(5, 2),
    antiguedad_meses INT,
    proveedor_preferente BOOLEAN DEFAULT FALSE,
    lista_restrictiva BOOLEAN DEFAULT FALSE,
    CONSTRAINT chk_proveedores_reclamos_nonneg CHECK (reclamos_asociados IS NULL OR reclamos_asociados >= 0),
    CONSTRAINT chk_proveedores_monto_prom_nonneg CHECK (monto_promedio_reclamado IS NULL OR monto_promedio_reclamado >= 0),
    CONSTRAINT chk_proveedores_pct_obs CHECK (porcentaje_casos_observados IS NULL OR (porcentaje_casos_observados >= 0 AND porcentaje_casos_observados <= 100)),
    CONSTRAINT chk_proveedores_antiguedad_nonneg CHECK (antiguedad_meses IS NULL OR antiguedad_meses >= 0)
);

-- 6. TABLA: BENEFICIARIOS
  CREATE TABLE beneficiarios (
    id_beneficiario VARCHAR(36) PRIMARY KEY,
    nombre_comercial TEXT NOT NULL,
    tipo_beneficiario VARCHAR(50) NOT NULL,
    ciudad VARCHAR(50),
    reclamos_asociados INT,
    monto_promedio_reclamado NUMERIC(12, 2),
    porcentaje_casos_observados NUMERIC(5, 2),
    antiguedad_meses INT,
  lista_restrictiva BOOLEAN DEFAULT FALSE,
    CONSTRAINT chk_beneficiarios_reclamos_nonneg CHECK (reclamos_asociados IS NULL OR reclamos_asociados >= 0),
    CONSTRAINT chk_beneficiarios_monto_prom_nonneg CHECK (monto_promedio_reclamado IS NULL OR monto_promedio_reclamado >= 0),
    CONSTRAINT chk_beneficiarios_pct_obs CHECK (porcentaje_casos_observados IS NULL OR (porcentaje_casos_observados >= 0 AND porcentaje_casos_observados <= 100)),
    CONSTRAINT chk_beneficiarios_antiguedad_nonneg CHECK (antiguedad_meses IS NULL OR antiguedad_meses >= 0)
  );

-- 6.1 TABLA: INTERMEDIARIOS / APS
CREATE TABLE intermediarios (
  id_intermediario VARCHAR(36) PRIMARY KEY,
  nombre_comercial TEXT NOT NULL,
  tipo_intermediario VARCHAR(50) NOT NULL,
  ciudad VARCHAR(50),
  lista_restrictiva BOOLEAN DEFAULT FALSE
);

  -- 7. TABLA: SINIESTROS (Corazon del analisis)
CREATE TABLE siniestros (
    id_siniestro VARCHAR(36) PRIMARY KEY,
    id_poliza VARCHAR(36) NOT NULL REFERENCES polizas(id_poliza),
    id_asegurado VARCHAR(36) NOT NULL REFERENCES asegurados(id_asegurado),
    id_proveedor VARCHAR(36) REFERENCES proveedores(id_proveedor),
    id_beneficiario VARCHAR(36) REFERENCES beneficiarios(id_beneficiario),
  id_intermediario VARCHAR(36) REFERENCES intermediarios(id_intermediario),
  id_conductor VARCHAR(36) REFERENCES conductores(id_conductor),
    id_vehiculo VARCHAR(36) REFERENCES vehiculos(id_vehiculo),
    codigo_siniestro VARCHAR(50) UNIQUE NOT NULL,

    ramo VARCHAR(30) NOT NULL,
    cobertura VARCHAR(50) NOT NULL,

    fecha_ocurrencia TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_reporte TIMESTAMP WITH TIME ZONE NOT NULL,

    monto_reclamado NUMERIC(12, 2) NOT NULL,
    monto_estimado NUMERIC(12, 2),
    monto_pagado NUMERIC(12, 2) DEFAULT 0.0,

    descripcion_narrativa TEXT NOT NULL,
    descripcion_embedding vector(384),

    estado_tramite VARCHAR(50) DEFAULT 'EN REVISION',
    score_riesgo INT DEFAULT 0,
    semaforo_alerta VARCHAR(20) DEFAULT 'VERDE',
    score_reglas INT DEFAULT 0,
    ml_proba DOUBLE PRECISION DEFAULT 0,
    ml_alerta INT DEFAULT 0,
    anom_score_0_1 DOUBLE PRECISION DEFAULT 0,
    explicacion_riesgo TEXT,

    causa_riesgo VARCHAR(100) NOT NULL,
    estado VARCHAR(20),
    sucursal VARCHAR(50),
    tipo_dinamica_accidente VARCHAR(50),
    tercero_identificado BOOLEAN DEFAULT TRUE,
    documentos_completos BOOLEAN DEFAULT TRUE,
    dias_desde_inicio_poliza INT,
    dias_desde_fin_poliza INT,
    dias_entre_ocurrencia_reporte INT,
    historial_siniestros_asegurado INT DEFAULT 0,
    etiqueta_fraude_simulada INT DEFAULT 0,
    CONSTRAINT chk_siniestros_montos_nonneg CHECK (
      monto_reclamado >= 0
      AND (monto_estimado IS NULL OR monto_estimado >= 0)
      AND monto_pagado >= 0
    ),
    CONSTRAINT chk_siniestros_fechas_reporte CHECK (fecha_reporte >= fecha_ocurrencia),
    CONSTRAINT chk_siniestros_dias_nonneg CHECK (
      (dias_desde_inicio_poliza IS NULL OR dias_desde_inicio_poliza >= 0)
      AND (dias_entre_ocurrencia_reporte IS NULL OR dias_entre_ocurrencia_reporte >= 0)
    ),
    CONSTRAINT chk_siniestros_score CHECK (score_riesgo BETWEEN 0 AND 100),
    CONSTRAINT chk_siniestros_score_reglas CHECK (score_reglas BETWEEN 0 AND 70),
    CONSTRAINT chk_siniestros_ml_proba CHECK (ml_proba >= 0 AND ml_proba <= 1),
    CONSTRAINT chk_siniestros_ml_alerta CHECK (ml_alerta IN (0, 1)),
    CONSTRAINT chk_siniestros_anom_score CHECK (anom_score_0_1 >= 0 AND anom_score_0_1 <= 1),
    CONSTRAINT chk_siniestros_historial_nonneg CHECK (historial_siniestros_asegurado >= 0),
    CONSTRAINT chk_siniestros_etiqueta_fraude CHECK (etiqueta_fraude_simulada IN (0, 1)),
    CONSTRAINT chk_siniestros_semaforo CHECK (semaforo_alerta IN ('VERDE', 'AMARILLO', 'ROJO'))
);

  -- 7. TABLA: CAMBIOS RECIENTES EN ASEGURADO
  CREATE TABLE cambios_asegurado (
    id_cambio VARCHAR(36) PRIMARY KEY,
    id_asegurado VARCHAR(36) NOT NULL REFERENCES asegurados(id_asegurado),
    campo_modificado VARCHAR(50) NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha_cambio TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

-- 8. TABLA: DOCUMENTOS
CREATE TABLE documentos (
    id_documento VARCHAR(36) PRIMARY KEY,
    id_siniestro VARCHAR(36) NOT NULL REFERENCES siniestros(id_siniestro),
    tipo_documento VARCHAR(50) NOT NULL,
    url_archivo TEXT NOT NULL,
    fecha_carga TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_emision TIMESTAMP WITH TIME ZONE,
    entregado BOOLEAN DEFAULT TRUE,
    es_legible BOOLEAN DEFAULT TRUE,
    posible_adulteracion BOOLEAN DEFAULT FALSE,
    inconsistencia_detectada BOOLEAN DEFAULT FALSE,
    observacion TEXT,
    CONSTRAINT chk_documentos_url_nonempty CHECK (length(trim(url_archivo)) > 0)
);

-- 9. FUNCION RPC PARA BUSQUEDA VECTORIAL (pgvector)
CREATE OR REPLACE FUNCTION buscar_narrativas_similares (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id_siniestro VARCHAR(36),
  codigo_siniestro VARCHAR(50),
  similitud float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id_siniestro,
    s.codigo_siniestro,
    1 - (s.descripcion_embedding <=> query_embedding) AS similitud
  FROM siniestros s
  WHERE 1 - (s.descripcion_embedding <=> query_embedding) > match_threshold
  ORDER BY s.descripcion_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 10. INDICES (Optimizacion)
DROP INDEX IF EXISTS idx_siniestros_active;
DROP INDEX IF EXISTS idx_siniestros_embedding;
CREATE INDEX idx_siniestros_embedding_hnsw ON siniestros USING hnsw (descripcion_embedding vector_cosine_ops);
CREATE INDEX idx_polizas_id_asegurado ON polizas(id_asegurado);
CREATE INDEX idx_siniestros_id_poliza ON siniestros(id_poliza);
CREATE INDEX idx_siniestros_id_asegurado ON siniestros(id_asegurado);
CREATE INDEX idx_siniestros_id_proveedor ON siniestros(id_proveedor);
CREATE INDEX idx_siniestros_id_beneficiario ON siniestros(id_beneficiario);
CREATE INDEX idx_siniestros_id_vehiculo ON siniestros(id_vehiculo);
CREATE INDEX idx_siniestros_id_conductor ON siniestros(id_conductor);
CREATE INDEX idx_siniestros_id_intermediario ON siniestros(id_intermediario);
CREATE INDEX idx_siniestros_ramo ON siniestros(ramo);
CREATE INDEX idx_siniestros_ciudad ON siniestros(sucursal);
CREATE INDEX idx_siniestros_semaforo ON siniestros(semaforo_alerta);
CREATE INDEX idx_cambios_asegurado_id ON cambios_asegurado(id_asegurado);
