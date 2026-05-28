from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.config import load_config
from src.ingestion.supabase_loader import create_supabase_client


def fetch_all_rows(
    supabase,
    table: str,
    page_size: int = 1000,
) -> List[Dict[str, Any]]:
    all_rows: List[Dict[str, Any]] = []
    offset = 0
    while True:
        resp = supabase.table(table).select("*").range(offset, offset + page_size - 1).execute()
        rows = resp.data or []
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return all_rows


def export_tables_to_csv(
    tables: Iterable[str],
    out_dir: Path,
    page_size: int = 1000,
) -> None:
    cfg = load_config(require_supabase=True)
    supabase = create_supabase_client(cfg)

    out_dir.mkdir(parents=True, exist_ok=True)

    for t in tables:
        rows = fetch_all_rows(supabase=supabase, table=t, page_size=page_size)
        df = pd.DataFrame(rows)
        df.to_csv(out_dir / f"{t}.csv", index=False)
        print(f"OK: {t}.csv ({len(df)} filas)")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("data") / "raw" / "supabase_export" / stamp
    export_tables_to_csv(
        tables=["asegurados", "polizas", "proveedores", "siniestros", "documentos"],
        out_dir=out_dir,
        page_size=1000,
    )
    print(f"\nExport completado en: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

