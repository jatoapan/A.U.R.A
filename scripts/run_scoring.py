from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.scoring import score_from_tables
from src.dataio.csv_exports import get_latest_export_dir, load_exported_tables


def main() -> None:
    export_dir = get_latest_export_dir(Path("data") / "raw" / "supabase_export")
    print(f"Export: {export_dir}")

    tables = load_exported_tables(export_dir)
    scored = score_from_tables(tables)

    out_path = Path("data") / "processed" / "siniestros_scored.csv"
    cols = [
        "id_siniestro",
        "codigo_siniestro",
        "score_reglas",
        "ml_proba",
        "ml_threshold",
        "ml_alerta",
        "anom_score_0_1",
        "score_final",
        "semaforo",
        "explicacion",
        "cobertura",
        "sucursal",
        "id_proveedor",
        "etiqueta_fraude_simulada",
    ]
    cols = [c for c in cols if c in scored.columns]
    scored[cols].to_csv(out_path, index=False)

    print(f"\nScoring guardado: {out_path.resolve()}")
    print("Semáforo:\n", scored["semaforo"].value_counts())
    print("\nTop 5 por score_final:")
    print(
        scored.sort_values("score_final", ascending=False)[
            ["codigo_siniestro", "score_final", "semaforo"]
        ].head(5)
    )


if __name__ == "__main__":
    main()
