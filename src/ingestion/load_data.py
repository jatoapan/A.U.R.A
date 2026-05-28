from __future__ import annotations

from .config import load_config
from .supabase_loader import borrar_datos_existentes, create_supabase_client, insertar_lotes
from .synthetic_generator import generate_synthetic_data

# =====================================================================
# FLUJO PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    print("INICIANDO INGESTIÓN INTELIGENTE DE DATOS SINTÉTICOS")
    cfg = load_config(require_supabase=True)

    print(f"Seed fija para generación sintética: {cfg.seed}")
    print("Generando dataset sintético (in-memory)...")
    generated = generate_synthetic_data(cfg)

    print("Conectando a Supabase...")
    supabase = create_supabase_client(cfg)

    print("Borrando datos existentes en Supabase (DELETE real)...")
    borrar_datos_existentes(supabase)

    print("Insertando datos...")
    counts = insertar_lotes(
        supabase=supabase,
        asegurados=generated.asegurados,
        polizas=generated.polizas,
        proveedores=generated.proveedores,
        siniestros=generated.siniestros,
        documentos=generated.documentos,
    )

    print("\n¡PROCESO COMPLETADO CON ÉXITO!")
    print("La base de datos está poblada y lista para auditar.")
    print(f"→ Filas insertadas: {dict(counts)}")
    print(f"→ ID del Taller Crítico (lista restrictiva): {generated.taller_critico_id}")
