from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.features.build_features import FEATURE_COLS_NUM

DEFAULT_ANOMALY_PATH = Path("data") / "processed" / "fraud_iso.joblib"


@dataclass
class AnomalyModel:
    """IsolationForest + normalización 0–1 (límites fijados en entrenamiento)."""

    iso: IsolationForest
    raw_min: float
    raw_max: float

    def predict_scores(self, X_num: pd.DataFrame) -> np.ndarray:
        X = X_num[FEATURE_COLS_NUM].copy()
        X = X.fillna(X.median(numeric_only=True))
        raw = -self.iso.score_samples(X)
        denom = self.raw_max - self.raw_min + 1e-9
        norm = (raw - self.raw_min) / denom
        return np.clip(norm, 0.0, 1.0)


def train_anomaly_model(
    X_num: pd.DataFrame,
    *,
    n_estimators: int = 300,
    contamination: float = 0.10,
    random_state: int = 42,
) -> AnomalyModel:
    X = X_num[FEATURE_COLS_NUM].copy()
    X = X.fillna(X.median(numeric_only=True))

    iso = IsolationForest(
        n_estimators=n_estimators,
        random_state=random_state,
        contamination=contamination,
    )
    iso.fit(X)
    raw = -iso.score_samples(X)
    return AnomalyModel(iso=iso, raw_min=float(raw.min()), raw_max=float(raw.max()))


def save_anomaly_model(model: AnomalyModel, path: Union[str, Path] = DEFAULT_ANOMALY_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_anomaly_model(path: Union[str, Path] = DEFAULT_ANOMALY_PATH) -> AnomalyModel:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"No existe modelo de anomalías en {path.resolve()}. "
            "Entrena con: python scripts/train_fraud_model.py"
        )
    return joblib.load(path)


def predict_anomaly_scores(
    model: AnomalyModel,
    X_num: pd.DataFrame,
) -> np.ndarray:
    return model.predict_scores(X_num)
