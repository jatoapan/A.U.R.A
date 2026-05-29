"""
Servicio de repositorio Supabase
"""
from typing import Dict, List, Optional
import pandas as pd
import re


class SupabaseRepository:
    """Acceso a datos en Supabase"""

    def __init__(self, client):
        self.client = client

    # ==================== Lectura ====================

    def fetch_siniestro(self, id_siniestro: str) -> Optional[Dict]:
        """Obtener un siniestro por ID"""
        try:
            response = self.client.table("siniestros").select("*").eq("id_siniestro", id_siniestro).execute()
            data = response.data
            return data[0] if data else None
        except Exception as e:
            raise Exception(f"Error fetching siniestro {id_siniestro}: {str(e)}")

    def list_siniestros(
        self,
        semaforo: Optional[str] = None,
        min_score: Optional[int] = None,
        cobertura: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "score_riesgo_desc",
    ) -> Dict[str, any]:
        """Listar siniestros con filtros"""
        try:
            # Base query
            q = self.client.table("siniestros").select("*")

            # Aplicar filtros
            if semaforo:
                q = q.eq("semaforo_alerta", semaforo)
            if min_score is not None:
                q = q.gte("score_riesgo", min_score)
            if cobertura:
                q = q.eq("cobertura", cobertura)

            # Contar total
            count_response = q.execute()
            total = len(count_response.data) if count_response.data else 0

            # Aplicar sorting
            if sort == "score_riesgo_desc":
                q = self.client.table("siniestros").select("*")
                if semaforo:
                    q = q.eq("semaforo_alerta", semaforo)
                if min_score is not None:
                    q = q.gte("score_riesgo", min_score)
                if cobertura:
                    q = q.eq("cobertura", cobertura)
                q = q.order("score_riesgo", desc=True)

            # Pagination
            q = q.limit(limit).offset(offset)
            response = q.execute()
            
            items = response.data or []
            return {"total": total, "items": items}
        except Exception as e:
            raise Exception(f"Error listing siniestros: {str(e)}")

    def fetch_scoring_tables(self, id_siniestro: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Obtener tablas necesarias para scoring (Supabase → pandas)"""
        try:
            q_sin = self.client.table("siniestros").select("*")
            q_pol = self.client.table("polizas").select("*")
            q_prov = self.client.table("proveedores").select("*")
            q_doc = self.client.table("documentos").select("*")

            if id_siniestro:
                q_sin = q_sin.eq("id_siniestro", id_siniestro)
                q_doc = q_doc.eq("id_siniestro", id_siniestro)

            siniestros = pd.DataFrame(q_sin.execute().data or [])
            polizas = pd.DataFrame(q_pol.execute().data or [])
            proveedores = pd.DataFrame(q_prov.execute().data or [])
            documentos = pd.DataFrame(q_doc.execute().data or [])

            return {
                "siniestros": siniestros,
                "polizas": polizas,
                "proveedores": proveedores,
                "documentos": documentos,
            }
        except Exception as e:
            raise Exception(f"Error fetching scoring tables: {str(e)}")

    # ==================== Escritura ====================

    def persist_score(self, id_siniestro: str, score_result: Dict) -> None:
        """Guardar score en Supabase"""
        payload = {
            "score_riesgo": int(score_result.get("score_final", 0)),
            "semaforo_alerta": str(score_result.get("semaforo", "VERDE")),
            "explicacion_riesgo": str(score_result.get("explicacion", "")),
            "ml_proba": float(score_result.get("ml_proba", 0)),
            "score_reglas": int(score_result.get("score_reglas", 0)),
            "ml_alerta": int(score_result.get("ml_alerta", 0)),
            "anom_score_0_1": float(score_result.get("anom_score_0_1", 0)),
        }

        # Supabase/PostgREST rechaza todo el PATCH si una columna no existe.
        # Durante desarrollo permitimos guardar al menos score_riesgo/semaforo_alerta
        # mientras se aplica la migracion de columnas analiticas.
        missing_col_pattern = re.compile(r"Could not find the '([^']+)' column")
        remaining_payload = dict(payload)
        missing_cols: List[str] = []

        while remaining_payload:
            try:
                self.client.table("siniestros").update(remaining_payload).eq("id_siniestro", id_siniestro).execute()
                return
            except Exception as e:
                match = missing_col_pattern.search(str(e))
                if not match:
                    raise Exception(f"Error persisting score for {id_siniestro}: {str(e)}")

                missing_col = match.group(1)
                if missing_col not in remaining_payload:
                    raise Exception(f"Error persisting score for {id_siniestro}: {str(e)}")

                missing_cols.append(missing_col)
                remaining_payload.pop(missing_col, None)

        raise Exception(
            f"Error persisting score for {id_siniestro}: no compatible columns found. "
            f"Missing columns: {missing_cols}"
        )

    def batch_persist_scores(self, scores_df) -> int:
        """Guardar múltiples scores (batch)"""
        try:
            count = 0
            for _, row in scores_df.iterrows():
                self.persist_score(row["id_siniestro"], row.to_dict())
                count += 1
            return count
        except Exception as e:
            raise Exception(f"Error in batch persist: {str(e)}")
