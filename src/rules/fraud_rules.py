from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

SCORE_MAX_REGLAS: int = 70


def calcular_semaforo(score_0_100: int) -> str:
    """Semáforo estándar del PDF."""
    if score_0_100 >= 76:
        return "ROJO"
    if score_0_100 >= 41:
        return "AMARILLO"
    return "VERDE"


def calcular_score_reglas(row: Any) -> Tuple[int, List[str]]:
    """Calcula score de reglas (0–70) + explicaciones.

    Espera columnas (según schema actual):
    - delta_vigencia_dias (o dias_desde_inicio_poliza)
    - delta_notificacion_dias (o dias_entre_ocurrencia_reporte)
    - cobertura
    - lista_restrictiva
    - doc_adulteracion / doc_inconsistencia
    - documentos_completos
    - historial_siniestros_asegurado
    - ratio_reclamado
    - max_similitud_narrativa (NLP)
    """
    if isinstance(row, dict):
        get = row.get
    else:
        # pandas Series / similar
        get = lambda k, default=None: row.get(k, default)  # type: ignore[assignment]

    pts = 0
    reasons: List[str] = []

    # RF-05: borde de vigencia extrema (<48 hrs) + señales del PDF por días
    dv = get("delta_vigencia_dias", get("dias_desde_inicio_poliza"))
    if dv is not None and pd.notna(dv):
        try:
            dv_i = float(dv)
        except Exception:
            dv_i = None
        if dv_i is not None:
            if dv_i <= 2:
                pts += 10
                reasons.append("RF-05: Borde de vigencia <48h (+10)")
            elif dv_i <= 10:
                pts += 8
                reasons.append("Borde de vigencia <=10d (+8)")
            elif dv_i <= 30:
                pts += 4
                reasons.append("Borde de vigencia 11–30d (+4)")

    # RF-06: demora atípica en denuncia de robo (>4 días)
    dr = get("delta_notificacion_dias", get("dias_entre_ocurrencia_reporte"))
    cobertura = get("cobertura")
    if dr is not None and pd.notna(dr):
        try:
            dr_i = float(dr)
        except Exception:
            dr_i = None
        if dr_i is not None:
            if (cobertura == "ROBO") and (dr_i > 4):
                pts += 8
                reasons.append("RF-06: Robo con reporte tardío >4d (+8)")
            elif dr_i > 7:
                pts += 5
                reasons.append("Reporte tardío >7d (+5)")
            elif 4 <= dr_i <= 7:
                pts += 3
                reasons.append("Reporte tardío 4–7d (+3)")

    # RF-03: proveedor en lista restrictiva
    if bool(get("lista_restrictiva", False)):
        pts += 10
        reasons.append("RF-03: Proveedor en lista restrictiva (+10)")

    # RF-02: evidencia documental
    if bool(get("doc_adulteracion", False)) or bool(get("doc_inconsistencia", False)):
        pts += 10
        reasons.append("RF-02: Evidencia documental (adulteración/inconsistencia) (+10)")
    elif get("documentos_completos") is False:
        pts += 4
        reasons.append("Docs incompletos (+4)")

    # Historial asegurado
    h = get("historial_siniestros_asegurado", 0)
    try:
        h_i = int(h)
    except Exception:
        h_i = 0
    if h_i >= 3:
        pts += 8
        reasons.append("Historial asegurado >=3 (+8)")
    elif h_i == 2:
        pts += 4
        reasons.append("Historial asegurado =2 (+4)")

    # Monto alto respecto a suma
    rr = get("ratio_reclamado")
    if rr is not None and pd.notna(rr):
        try:
            rr_f = float(rr)
        except Exception:
            rr_f = None
        if rr_f is not None:
            if rr_f >= 0.95:
                pts += 5
                reasons.append("Reclamo >=95% suma asegurada (+5)")
            elif rr_f >= 0.70:
                pts += 3
                reasons.append("Reclamo >=70% suma asegurada (+3)")

    # RF-07: narrativa idéntica/clonada (NLP)
    ms = get("max_similitud_narrativa", 0.0) or 0.0
    if ms is not None and pd.notna(ms):
        try:
            ms_f = float(ms)
        except Exception:
            ms_f = 0.0
        if ms_f >= 0.85:
            pts += 8
            reasons.append(f"RF-07: Narrativa similar (max_sim={ms_f:.2f}) (+8)")
        elif ms_f >= 0.70:
            pts += 4
            reasons.append(f"Narrativa moderadamente similar (max_sim={ms_f:.2f}) (+4)")

    return int(min(pts, SCORE_MAX_REGLAS)), reasons