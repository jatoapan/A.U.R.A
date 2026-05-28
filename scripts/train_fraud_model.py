from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from src.dataio.csv_exports import get_latest_export_dir, load_exported_tables
from src.features.build_features import FEATURE_COLS_NUM, LABEL_COL, build_from_tables, prepare_ml_matrix
from src.models.anomaly_model import DEFAULT_ANOMALY_PATH, save_anomaly_model, train_anomaly_model
from src.models.fraud_model import (
    DEFAULT_C,
    DEFAULT_MODEL_PATH,
    OPERATIONAL_ML_THRESHOLD,
    predict_fraud_proba,
    select_threshold_max_f1,
    train_and_save,
)


def main() -> None:
    export_dir = get_latest_export_dir(Path("data") / "raw" / "supabase_export")
    print(f"Export: {export_dir}")

    tables = load_exported_tables(export_dir)
    df = build_from_tables(tables)
    X, y = prepare_ml_matrix(df)

    if y is None:
        raise RuntimeError(f"Falta columna {LABEL_COL} para entrenar.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Parámetros fijos notebook 03: C=0.1 (CV), threshold operativo 0.7
    model, path, cfg = train_and_save(
        X_train,
        y_train,
        X_test,
        y_test,
        path=DEFAULT_MODEL_PATH,
        tune_c=False,
        C=DEFAULT_C,
    )
    proba = predict_fraud_proba(model, X_test)

    anom = train_anomaly_model(X[FEATURE_COLS_NUM])
    anom_path = save_anomaly_model(anom, DEFAULT_ANOMALY_PATH)

    thr_f1 = select_threshold_max_f1(y_test, proba)
    print(f"\nModelo ML guardado: {path.resolve()}")
    print(
        f"Config (prod=nb03): C={cfg.C}, threshold={cfg.ml_threshold} "
        f"(max F1 holdout C=0.1 sería {thr_f1:.2f}, no usado en prod)"
    )
    print(f"Modelo anomalías guardado: {anom_path.resolve()}")
    print("AUC-ROC (test):", roc_auc_score(y_test, proba))
    print(f"\nReporte (threshold={cfg.ml_threshold}):")
    print(classification_report(y_test, (proba >= cfg.ml_threshold).astype(int), zero_division=0))


if __name__ == "__main__":
    main()
