from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd


def get_latest_export_dir(base_dir: str | Path = Path("data") / "raw" / "supabase_export") -> Path:
    base = Path(base_dir)
    if not base.exists():
        raise FileNotFoundError(f"No existe el directorio de export: {base.resolve()}")

    candidates = [p for p in base.iterdir() if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No hay exports dentro de: {base.resolve()}")

    # nombre timestamp YYYYMMDD_HHMMSS => orden lexicográfico funciona
    candidates.sort(key=lambda p: p.name)
    return candidates[-1]


def load_exported_tables(
    export_dir: str | Path,
    *,
    tables: Optional[list[str]] = None,
) -> Dict[str, pd.DataFrame]:
    export_path = Path(export_dir)
    if tables is None:
        tables = ["asegurados", "polizas", "proveedores", "siniestros", "documentos"]

    out: Dict[str, pd.DataFrame] = {}
    for t in tables:
        csv_path = export_path / f"{t}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Falta CSV esperado: {csv_path.resolve()}")
        out[t] = pd.read_csv(csv_path)
    return out

