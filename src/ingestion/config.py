import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _get_env(name: str, default: str) -> str:
    v = os.getenv(name)
    return default if v is None or v == "" else v


@dataclass(frozen=True)
class IngestionConfig:
    supabase_url: str
    supabase_key: str

    seed: int
    n_asegurados: int
    n_proveedores: int

    suspect_provider_rate: float
    suspect_provider_min: int
    suspect_provider_max: int
    fraud_to_suspect_prob: float
    normal_to_suspect_prob: float

    fraud_rate: float
    fraud_near_start_prob: float
    near_start_days_max: int
    normal_days_since_start_min: int
    normal_days_since_start_max: int

    fraud_late_report_prob: float
    late_report_days_min: int
    late_report_days_max: int
    normal_report_days_min: int
    normal_report_days_max: int

    narrative_clone_prob: float

    docs_complete_prob_fraud_robo: float
    docs_complete_prob_normal_robo: float
    docs_complete_prob_fraud_no_robo: float
    docs_complete_prob_normal_no_robo: float

    fraud_high_history_prob: float
    history_fraud_min: int
    history_fraud_max: int
    history_normal_min: int
    history_normal_max: int

    coverage_weight_choque: float
    coverage_weight_robo: float
    coverage_weight_danos: float

    doc_suspicious_prob: float

    monto_estimado_factor_min: float
    monto_estimado_factor_max: float

    docs_per_claim_min: int
    docs_per_claim_max: int


def load_config(require_supabase: bool = True) -> IngestionConfig:
    load_dotenv()

    supabase_url = _get_env("SUPABASE_URL", "")
    supabase_key = _get_env("SUPABASE_KEY", "")

    if require_supabase and (not supabase_url or not supabase_key):
        raise EnvironmentError(
            "Faltan variables de entorno. Crea un archivo .env con SUPABASE_URL y SUPABASE_KEY."
        )

    return IngestionConfig(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        seed=int(_get_env("AURA_SEED", "42")),
        n_asegurados=int(_get_env("AURA_N_ASEGURADOS", "1000")),
        n_proveedores=int(_get_env("AURA_N_PROVEEDORES", "50")),
        suspect_provider_rate=float(_get_env("AURA_SUSPECT_PROVIDER_RATE", "0.08")),
        suspect_provider_min=int(_get_env("AURA_SUSPECT_PROVIDER_MIN", "2")),
        suspect_provider_max=int(_get_env("AURA_SUSPECT_PROVIDER_MAX", "8")),
        fraud_to_suspect_prob=float(_get_env("AURA_FRAUD_TO_SUSPECT_PROB", "0.40")),
        normal_to_suspect_prob=float(_get_env("AURA_NORMAL_TO_SUSPECT_PROB", "0.08")),
        fraud_rate=float(_get_env("AURA_FRAUD_RATE", "0.15")),
        fraud_near_start_prob=float(_get_env("AURA_FRAUD_NEAR_START_PROB", "0.70")),
        near_start_days_max=int(_get_env("AURA_NEAR_START_DAYS_MAX", "5")),
        normal_days_since_start_min=int(_get_env("AURA_NORMAL_DAYS_SINCE_START_MIN", "10")),
        normal_days_since_start_max=int(_get_env("AURA_NORMAL_DAYS_SINCE_START_MAX", "200")),
        fraud_late_report_prob=float(_get_env("AURA_FRAUD_LATE_REPORT_PROB", "0.70")),
        late_report_days_min=int(_get_env("AURA_LATE_REPORT_DAYS_MIN", "5")),
        late_report_days_max=int(_get_env("AURA_LATE_REPORT_DAYS_MAX", "15")),
        normal_report_days_min=int(_get_env("AURA_NORMAL_REPORT_DAYS_MIN", "1")),
        normal_report_days_max=int(_get_env("AURA_NORMAL_REPORT_DAYS_MAX", "3")),
        narrative_clone_prob=float(_get_env("AURA_NARRATIVE_CLONE_PROB", "0.20")),
        docs_complete_prob_fraud_robo=float(_get_env("AURA_DOCS_COMPLETE_PROB_FRAUD_ROBO", "0.55")),
        docs_complete_prob_normal_robo=float(_get_env("AURA_DOCS_COMPLETE_PROB_NORMAL_ROBO", "0.80")),
        docs_complete_prob_fraud_no_robo=float(_get_env("AURA_DOCS_COMPLETE_PROB_FRAUD_NO_ROBO", "0.65")),
        docs_complete_prob_normal_no_robo=float(_get_env("AURA_DOCS_COMPLETE_PROB_NORMAL_NO_ROBO", "0.90")),
        fraud_high_history_prob=float(_get_env("AURA_FRAUD_HIGH_HISTORY_PROB", "0.80")),
        history_fraud_min=int(_get_env("AURA_HISTORY_FRAUD_MIN", "2")),
        history_fraud_max=int(_get_env("AURA_HISTORY_FRAUD_MAX", "5")),
        history_normal_min=int(_get_env("AURA_HISTORY_NORMAL_MIN", "0")),
        history_normal_max=int(_get_env("AURA_HISTORY_NORMAL_MAX", "2")),
        coverage_weight_choque=float(_get_env("AURA_COVERAGE_WEIGHT_CHOQUE", "0.34")),
        coverage_weight_robo=float(_get_env("AURA_COVERAGE_WEIGHT_ROBO", "0.33")),
        coverage_weight_danos=float(_get_env("AURA_COVERAGE_WEIGHT_DANOS", "0.33")),
        doc_suspicious_prob=float(_get_env("AURA_DOC_SUSPICIOUS_PROB", "0.05")),
        monto_estimado_factor_min=float(_get_env("AURA_MONTO_ESTIMADO_FACTOR_MIN", "0.85")),
        monto_estimado_factor_max=float(_get_env("AURA_MONTO_ESTIMADO_FACTOR_MAX", "1.10")),
        docs_per_claim_min=int(_get_env("AURA_DOCS_PER_CLAIM_MIN", "1")),
        docs_per_claim_max=int(_get_env("AURA_DOCS_PER_CLAIM_MAX", "3")),
    )

