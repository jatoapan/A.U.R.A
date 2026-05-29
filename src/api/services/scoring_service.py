"""
Servicio de scoring - wrapper para el motor Python
"""
from pathlib import Path
import sys
from typing import Dict, Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.scoring import score_dataframe, score_from_tables
from src.features.build_features import build_from_tables


class ScoringService:
    """Servicio que encapsula la lógica de scoring"""

    def __init__(self, ml_model, anomaly_model, ml_config):
        self.ml_model = ml_model
        self.anomaly_model = anomaly_model
        self.ml_config = ml_config

    def score_one_claim(self, tables: Dict[str, pd.DataFrame], id_siniestro: str) -> Dict[str, Any]:
        """Calcular score para UN siniestro"""
        try:
            # Construir features desde tablas
            df = build_from_tables(tables)
            df = df[df["id_siniestro"] == id_siniestro]

            if df.empty:
                raise ValueError(f"Siniestro no encontrado: {id_siniestro}")

            # Aplicar pipeline de scoring
            scored = score_dataframe(
                df,
                ml_model=self.ml_model,
                anomaly_model=self.anomaly_model,
                apply_nlp=True,
            )

            result = scored.iloc[0].to_dict()
            return result

        except Exception as e:
            raise Exception(f"Error scoring claim {id_siniestro}: {str(e)}")

    def score_batch(self, tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calcular score para TODOS los siniestros"""
        try:
            df = build_from_tables(tables)
            scored = score_dataframe(
                df,
                ml_model=self.ml_model,
                anomaly_model=self.anomaly_model,
                apply_nlp=True,
            )
            return scored
        except Exception as e:
            raise Exception(f"Error in batch scoring: {str(e)}")

    def get_semaforo_counts(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Contar siniestros por semáforo"""
        try:
            scored = self.score_batch(tables)
            counts = scored["semaforo"].value_counts().to_dict()
            return {"VERDE": counts.get("VERDE", 0), "AMARILLO": counts.get("AMARILLO", 0), "ROJO": counts.get("ROJO", 0)}
        except Exception as e:
            raise Exception(f"Error getting semaforo counts: {str(e)}")
