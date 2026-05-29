"""
Dependencias inyectables para A.U.R.A API
"""
import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno desde .env
# Busca .env en la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class SupabaseClient:
    """Cliente Supabase singleton"""
    _instance: Optional["SupabaseClient"] = None

    def __init__(self):
        if SupabaseClient._instance is not None:
            raise RuntimeError("Use SupabaseClient.get() para obtener la instancia")
        
        # Leer variables y limpiar comillas si las tienen
        self.url = os.environ.get("SUPABASE_URL", "").strip().strip('"').strip("'")
        self.key = os.environ.get("SUPABASE_KEY", "").strip().strip('"').strip("'")
        
        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL y SUPABASE_KEY requeridos en .env\n"
                f"Verificar: {env_path}"
            )
        
        self.client = create_client(self.url, self.key)

    @staticmethod
    def get():
        """Obtener instancia singleton"""
        if SupabaseClient._instance is None:
            SupabaseClient._instance = SupabaseClient()
        return SupabaseClient._instance.client

    @staticmethod
    def reset():
        """Reset para testing"""
        SupabaseClient._instance = None


@lru_cache(maxsize=1)
def get_supabase_client():
    """Dependency: cliente Supabase"""
    return SupabaseClient.get()
