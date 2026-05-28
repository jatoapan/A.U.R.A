from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

from src.explainability.explain_score import build_explanation
from src.features.build_features import (
    FEATURE_COLS_NUM,
    build_from_tables,
    prepare_ml_matrix,
)
from src.models.anomaly_model import (
    DEFAULT_ANOMALY_PATH,
    load_anomaly_model,
    predict_anomaly_scores,
)
from src.models.fraud_model import (
    DEFAULT_MODEL_PATH,
    load_model,
    load_model_config,
    predict_fraud_proba,
)
from src.nlp.narrative_similarity import add_narrative_similarity_features
from src.rules.fraud_rules import SCORE_MAX_REGLAS, calcular_score_reglas, calcular_semaforo

# Pesos score final (notebook 02 / PDF referencial)
W_RULES = 70
W_ML = 20
W_ANOM = 10


def apply_nlp_layer(df: pd.DataFrame) -> pd.DataFrame:
    """Capa NLP → alimenta reglas (RF-07)."""
    return add_narrative_similarity_features(df)


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Capa reglas de negocio (incluye RF-07 vía max_similitud_narrativa)."""
    out = df.copy()
    rules = out.apply(calcular_score_reglas, axis=1)
    out["score_reglas"] = [x[0] for x in rules]
    out["razones_reglas"] = [x[1] for x in rules]
    return out


def compute_hybrid_score(
    score_reglas: pd.Series,
    ml_proba: pd.Series,
    anom_score: pd.Series,
) -> pd.Series:
    return (
        (score_reglas.clip(0, SCORE_MAX_REGLAS) / float(SCORE_MAX_REGLAS)) * W_RULES
        + ml_proba.clip(0, 1) * W_ML
        + anom_score.clip(0, 1) * W_ANOM
    ).round(0).astype(int).clip(0, 100)


def score_dataframe(
    df: pd.DataFrame,
    *,
    ml_model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
    anomaly_model_path: Union[str, Path] = DEFAULT_ANOMALY_PATH,
    ml_model=None,
    anomaly_model=None,
    apply_nlp: bool = True,
) -> pd.DataFrame:
    """
    Pipeline híbrido PDF (3 capas + combinación):

    1. NLP  → max_similitud_narrativa
    2. Reglas → score_reglas (0–70)
    3. ML tabular → ml_proba (sin NLP)
    4. Anomalías → anom_score_0_1
    5. score_final + semáforo + explicación
    """
    out = df.copy()
    if apply_nlp:
        out = apply_nlp_layer(out)

    out = apply_rules(out)

    X, _ = prepare_ml_matrix(out)

    cfg = load_model_config()

    if ml_model is None:
        ml_model = load_model(ml_model_path)
    if anomaly_model is None:
        anomaly_model = load_anomaly_model(anomaly_model_path)

    out["ml_proba"] = predict_fraud_proba(ml_model, X)
    out["ml_threshold"] = cfg.ml_threshold
    out["ml_alerta"] = (out["ml_proba"] >= cfg.ml_threshold).astype(int)
    out["anom_score_0_1"] = predict_anomaly_scores(anomaly_model, X[FEATURE_COLS_NUM])

    out["score_final"] = compute_hybrid_score(
        out["score_reglas"],
        out["ml_proba"],
        out["anom_score_0_1"],
    )
    out["semaforo"] = out["score_final"].apply(calcular_semaforo)
    out["explicacion"] = out.apply(build_explanation, axis=1)

    return out


def score_from_tables(tables: Dict[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
    df = build_from_tables(tables)
    return score_dataframe(df, **kwargs)
