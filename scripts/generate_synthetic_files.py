from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.config import load_config
from src.ingestion.synthetic_generator import generate_synthetic_data


def main() -> None:
    cfg = load_config(require_supabase=False)
    generated = generate_synthetic_data(cfg)

    out_dir = Path("data") / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(generated.asegurados).to_csv(out_dir / "asegurados.csv", index=False)
    pd.DataFrame(generated.polizas).to_csv(out_dir / "polizas.csv", index=False)
    pd.DataFrame(generated.proveedores).to_csv(out_dir / "proveedores.csv", index=False)
    pd.DataFrame(generated.siniestros).to_csv(out_dir / "siniestros.csv", index=False)
    pd.DataFrame(generated.documentos).to_csv(out_dir / "documentos.csv", index=False)

    print(f"OK: generados CSVs en {out_dir.resolve()}")
    print(f"→ Taller crítico (lista restrictiva): {generated.taller_critico_id}")


if __name__ == "__main__":
    main()

