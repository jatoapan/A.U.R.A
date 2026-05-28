from __future__ import annotations

from typing import Any, List

import pandas as pd


def build_explanation(row: Any, *, max_items: int = 6) -> str:
    """Texto corto para el analista: reglas + ML + anomalía."""
    if isinstance(row, dict):
        razones: List[str] = list(row.get("razones_reglas") or [])
        ml = row.get("ml_proba", 0)
        anom = row.get("anom_score_0_1", 0)
    else:
        razones = list(row.get("razones_reglas") or [])
        ml = row.get("ml_proba", 0)
        anom = row.get("anom_score_0_1", 0)

    thr = row.get("ml_threshold")
    ml_txt = f"ML prob={float(ml):.2f}"
    if thr is not None and float(ml) >= float(thr):
        ml_txt += " (alerta)"
    razones.append(ml_txt)
    razones.append(f"Anomalía={float(anom):.2f}")
    return " | ".join(razones[:max_items])
