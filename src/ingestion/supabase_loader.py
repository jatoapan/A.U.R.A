from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from supabase import Client, create_client

from .config import IngestionConfig


@dataclass(frozen=True)
class LoadResult:
    taller_critico_id: str
    rows_inserted: Mapping[str, int]


def create_supabase_client(cfg: IngestionConfig) -> Client:
    return create_client(cfg.supabase_url, cfg.supabase_key)


def borrar_datos_existentes(supabase: Client) -> None:
    tablas_y_pk = {
        "documentos": "id_documento",
        "siniestros": "id_siniestro",
        "proveedores": "id_proveedor",
        "polizas": "id_poliza",
        "asegurados": "id_asegurado",
    }
    for tabla, pk in tablas_y_pk.items():
        # DELETE real (no soft delete)
        supabase.table(tabla).delete().neq(pk, "").execute()


def insertar_lotes(
    supabase: Client,
    asegurados: List[Dict[str, Any]],
    polizas: List[Dict[str, Any]],
    proveedores: List[Dict[str, Any]],
    siniestros: List[Dict[str, Any]],
    documentos: List[Dict[str, Any]],
) -> Mapping[str, int]:
    counts: Dict[str, int] = {}
    if asegurados:
        supabase.table("asegurados").insert(asegurados).execute()
    counts["asegurados"] = len(asegurados)

    if polizas:
        supabase.table("polizas").insert(polizas).execute()
    counts["polizas"] = len(polizas)

    if proveedores:
        supabase.table("proveedores").insert(proveedores).execute()
    counts["proveedores"] = len(proveedores)

    if siniestros:
        supabase.table("siniestros").insert(siniestros).execute()
    counts["siniestros"] = len(siniestros)

    if documentos:
        supabase.table("documentos").insert(documentos).execute()
    counts["documentos"] = len(documentos)

    return counts

