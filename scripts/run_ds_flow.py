from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    # 1) Genera + carga sintética a Supabase
    runpy.run_module("src.ingestion.load_data", run_name="__main__")

    # 2) Exporta Supabase -> CSVs
    runpy.run_path("scripts/export_supabase_to_csv.py", run_name="__main__")


if __name__ == "__main__":
    main()

