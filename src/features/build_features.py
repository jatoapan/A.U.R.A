from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

LABEL_COL = "etiqueta_fraude_simulada"

# Features tabulares para ML (PDF: ML supervisado separado de NLP)
FEATURE_COLS_NUM: List[str] = [
    "monto_reclamado",
    "monto_estimado",
    "ratio_reclamado",
    "delta_notificacion_dias",
    "delta_vigencia_dias",
    "historial_siniestros_asegurado",
    "doc_count",
    "doc_inconsistencia",
    "doc_adulteracion",
    "doc_ilegible",
    "doc_faltante",
]

FEATURE_COLS_CAT: List[str] = ["cobertura", "sucursal", "tipo_proveedor"]
FEATURE_COLS_BOOL: List[str] = ["documentos_completos", "lista_restrictiva", "proveedor_preferente"]
FEATURE_COLS_ALL: List[str] = FEATURE_COLS_NUM + FEATURE_COLS_CAT + FEATURE_COLS_BOOL


def build_master_dataframe(
    df_siniestros: pd.DataFrame,
    df_polizas: pd.DataFrame,
    df_proveedores: pd.DataFrame,
    df_documentos: pd.DataFrame,
) -> pd.DataFrame:
    """Une tablas y crea features tabulares (sin capa NLP)."""
    pol_cols = [
        c
        for c in [
            "id_poliza",
            "monto_asegurado",
            "tipo_cobertura",
            "ramo",
            "ciudad",
            "estado_poliza",
            "deducible",
            "prima",
        ]
        if c in df_polizas.columns
    ]
    df = df_siniestros.merge(
        df_polizas[pol_cols] if pol_cols else df_polizas,
        on="id_poliza",
        how="left",
        suffixes=("", "_pol"),
    )

    prov_cols = [
        c
        for c in [
            "id_proveedor",
            "tipo_proveedor",
            "ciudad",
            "lista_restrictiva",
            "proveedor_preferente",
        ]
        if c in df_proveedores.columns
    ]
    df = df.merge(
        df_proveedores[prov_cols] if prov_cols else df_proveedores,
        on="id_proveedor",
        how="left",
        suffixes=("", "_prov"),
    )

    if not df_documentos.empty and "id_siniestro" in df_documentos.columns:
        doc = df_documentos.copy()
        for c in ["posible_adulteracion", "inconsistencia_detectada", "es_legible", "entregado"]:
            if c not in doc.columns:
                doc[c] = False

        agg = doc.groupby("id_siniestro").agg(
            doc_count=("id_documento", "count"),
            doc_inconsistencia=("inconsistencia_detectada", "max"),
            doc_adulteracion=("posible_adulteracion", "max"),
            doc_entregado=("entregado", "min"),
            doc_es_legible=("es_legible", "min"),
        )
        agg["doc_ilegible"] = (~agg["doc_es_legible"].astype(bool)).astype(int)
        agg["doc_faltante"] = (~agg["doc_entregado"].astype(bool)).astype(int)
        df = df.merge(agg.reset_index(), on="id_siniestro", how="left")

    if {"monto_reclamado", "monto_asegurado"}.issubset(df.columns):
        df["ratio_reclamado"] = df["monto_reclamado"] / df["monto_asegurado"]

    df["delta_notificacion_dias"] = df.get("dias_entre_ocurrencia_reporte", np.nan)
    df["delta_vigencia_dias"] = df.get("dias_desde_inicio_poliza", np.nan)

    for c in ["doc_count", "doc_inconsistencia", "doc_adulteracion", "doc_ilegible", "doc_faltante"]:
        if c in df.columns:
            df[c] = df[c].fillna(0)

    return df


def prepare_ml_matrix(
    df: pd.DataFrame,
    *,
    label_col: str = LABEL_COL,
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """Matriz X solo con features tabulares (sin NLP)."""
    work = df.copy()
    for c in FEATURE_COLS_NUM:
        if c not in work.columns:
            work[c] = np.nan
    for c in FEATURE_COLS_CAT:
        if c not in work.columns:
            work[c] = None
    for c in FEATURE_COLS_BOOL:
        if c not in work.columns:
            work[c] = False

    X = work[FEATURE_COLS_ALL].copy()
    for c in FEATURE_COLS_BOOL:
        X[c] = X[c].fillna(False).astype(int)

    y = None
    if label_col in work.columns:
        y = work[label_col].astype(int)

    return X, y


def build_from_tables(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Tablas exportadas → df maestro tabular (sin NLP)."""
    return build_master_dataframe(
        tables["siniestros"],
        tables["polizas"],
        tables["proveedores"],
        tables["documentos"],
    )
