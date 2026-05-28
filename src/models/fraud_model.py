from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features.build_features import (
    FEATURE_COLS_ALL,
    FEATURE_COLS_BOOL,
    FEATURE_COLS_CAT,
    FEATURE_COLS_NUM,
)

DEFAULT_MODEL_PATH = Path("data") / "processed" / "fraud_lr.joblib"
DEFAULT_CONFIG_PATH = Path("data") / "processed" / "fraud_model_config.json"

# Hiperparámetros elegidos en notebook 03 (evaluación + CV)
DEFAULT_MODEL_NAME = "LogisticRegression"
DEFAULT_C = 0.1
# Umbral operativo nb03 (fijo en prod; no recalibrar con C=0.1 → daría ~0.75)
OPERATIONAL_ML_THRESHOLD = 0.7
DEFAULT_ML_THRESHOLD = OPERATIONAL_ML_THRESHOLD
CV_CS = [0.1, 0.3, 1.0, 3.0, 10.0]
TRAIN_RANDOM_STATE = 42
TEST_SIZE = 0.25


@dataclass
class FraudModelConfig:
    model_name: str = DEFAULT_MODEL_NAME
    C: float = DEFAULT_C
    ml_threshold: float = DEFAULT_ML_THRESHOLD
    random_state: int = TRAIN_RANDOM_STATE
    test_size: float = TEST_SIZE
    feature_cols: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.feature_cols is None:
            self.feature_cols = list(FEATURE_COLS_ALL)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imp", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                FEATURE_COLS_NUM,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imp", SimpleImputer(strategy="most_frequent")),
                        ("oh", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                FEATURE_COLS_CAT,
            ),
            (
                "bool",
                Pipeline(steps=[("imp", SimpleImputer(strategy="most_frequent"))]),
                FEATURE_COLS_BOOL,
            ),
        ]
    )


def build_pipeline(*, C: float = DEFAULT_C) -> Pipeline:
    return Pipeline(
        steps=[
            ("pre", build_preprocessor()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    C=C,
                ),
            ),
        ]
    )


def select_C_by_cv(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    Cs: Optional[list[float]] = None,
    n_splits: int = 5,
    random_state: int = TRAIN_RANDOM_STATE,
) -> float:
    from sklearn.metrics import roc_auc_score

    if Cs is None:
        Cs = list(CV_CS)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    best_c, best_auc = Cs[0], -1.0

    for c in Cs:
        aucs = []
        for train_idx, val_idx in skf.split(X, y):
            Xt, Xv = X.iloc[train_idx], X.iloc[val_idx]
            yt, yv = y.iloc[train_idx], y.iloc[val_idx]
            m = build_pipeline(C=c)
            m.fit(Xt, yt)
            pv = m.predict_proba(Xv)[:, 1]
            aucs.append(roc_auc_score(yv, pv))
        mean_auc = float(np.mean(aucs))
        if mean_auc > best_auc:
            best_auc = mean_auc
            best_c = c

    return float(best_c)


def select_threshold_max_f1(
    y_true: pd.Series,
    proba: np.ndarray,
    *,
    thresholds: Optional[np.ndarray] = None,
) -> float:
    """Misma lógica que notebook 03: umbral que maximiza F1 en holdout."""
    if thresholds is None:
        thresholds = np.linspace(0.05, 0.95, 19)

    best_t, best_f1 = float(DEFAULT_ML_THRESHOLD), -1.0
    y = y_true.astype(int).values

    for t in thresholds:
        pred = (proba >= t).astype(int)
        cm = confusion_matrix(y, pred)
        tn, fp, fn, tp = cm.ravel()
        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)

    return best_t


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    C: Optional[float] = None,
    tune_c: bool = False,
) -> Pipeline:
    if tune_c:
        C = select_C_by_cv(X, y)
    elif C is None:
        C = DEFAULT_C

    model = build_pipeline(C=C)
    model.fit(X, y)
    return model


def predict_fraud_proba(model: Pipeline, X: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def predict_fraud_flag(
    model: Pipeline,
    X: pd.DataFrame,
    *,
    threshold: float = DEFAULT_ML_THRESHOLD,
) -> np.ndarray:
    return (predict_fraud_proba(model, X) >= threshold).astype(int)


def save_model(model: Pipeline, path: Union[str, Path] = DEFAULT_MODEL_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def save_model_config(
    config: FraudModelConfig,
    path: Union[str, Path] = DEFAULT_CONFIG_PATH,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    return path


def load_model(path: Union[str, Path] = DEFAULT_MODEL_PATH) -> Pipeline:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el modelo en {path.resolve()}. "
            "Entrena con: python scripts/train_fraud_model.py"
        )
    return joblib.load(path)


def load_model_config(path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> FraudModelConfig:
    path = Path(path)
    if not path.exists():
        return FraudModelConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    return FraudModelConfig(**data)


def train_and_save(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_eval: pd.DataFrame,
    y_eval: pd.Series,
    *,
    path: Union[str, Path] = DEFAULT_MODEL_PATH,
    config_path: Union[str, Path] = DEFAULT_CONFIG_PATH,
    tune_c: bool = False,
    C: Optional[float] = None,
) -> tuple[Pipeline, Path, FraudModelConfig]:
    """Entrena con C y umbral operativo del notebook 03; guarda joblib + config JSON."""
    if tune_c:
        C = select_C_by_cv(X_train, y_train)
    elif C is None:
        C = DEFAULT_C

    model = build_pipeline(C=C)
    model.fit(X_train, y_train)

    config = FraudModelConfig(
        model_name=DEFAULT_MODEL_NAME,
        C=float(C),
        ml_threshold=float(OPERATIONAL_ML_THRESHOLD),
    )

    saved = save_model(model, path)
    save_model_config(config, config_path)
    return model, saved, config
