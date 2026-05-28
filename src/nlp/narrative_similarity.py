from __future__ import annotations

import ast

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def add_narrative_similarity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Capa NLP (PDF §9): similitud semántica entre narrativas con cruce de entidades.

    Salida: columna `max_similitud_narrativa` usada por **reglas** (RF-07), no por ML.
    """
    if "descripcion_embedding" not in df.columns:
        out = df.copy()
        out["max_similitud_narrativa"] = 0.0
        return out

    def _emb(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        if isinstance(v, str):
            return np.array(ast.literal_eval(v))
        return np.array(v)

    tmp = df[["id_siniestro", "id_asegurado", "id_proveedor", "descripcion_embedding"]].copy()
    tmp["emb"] = tmp["descripcion_embedding"].apply(_emb)
    tmp = tmp[tmp["emb"].notnull()].copy()

    out = df.copy()
    if len(tmp) <= 1:
        out["max_similitud_narrativa"] = 0.0
        return out

    E = np.stack(tmp["emb"].values)
    S = cosine_similarity(E)
    np.fill_diagonal(S, -1.0)

    max_sim = np.zeros(len(tmp), dtype=float)
    aseg = tmp["id_asegurado"].values
    prov = tmp["id_proveedor"].values
    for i in range(len(tmp)):
        mask = (aseg != aseg[i]) | (prov != prov[i])
        max_sim[i] = float(S[i, mask].max()) if mask.any() else 0.0

    tmp["max_similitud_narrativa"] = max_sim
    out = out.drop(columns=["max_similitud_narrativa"], errors="ignore")
    out = out.merge(tmp[["id_siniestro", "max_similitud_narrativa"]], on="id_siniestro", how="left")
    out["max_similitud_narrativa"] = out["max_similitud_narrativa"].fillna(0.0)
    return out
