import os
import math
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Faltan variables de entorno. Crea un archivo .env con SUPABASE_URL y SUPABASE_KEY."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# LÍMITES DE SCORE POR MÓDULO
# Motor de Reglas (Paso 2.1) → hasta 70 pts  (ya guardado en Supabase)
# Módulo ML              → hasta 15 pts  (este archivo)
# Módulo NLP             → hasta 15 pts  (este archivo)
# TOTAL MÁXIMO           → 100 pts
# =====================================================================
SCORE_MAX_ML:  int = 15
SCORE_MAX_NLP: int = 15
SCORE_MAX_TOTAL: int = 100

# Umbral de similitud para considerar una narrativa "clonada"
UMBRAL_SIMILITUD_NLP: float = 0.85

# =====================================================================
# UTILIDADES MATEMÁTICAS
# Sin dependencia de numpy — todo con math de la stdlib.
# =====================================================================

def _dot_product(a: List[float], b: List[float]) -> float:
    """Producto punto entre dos vectores."""
    return sum(x * y for x, y in zip(a, b))

def _norma(v: List[float]) -> float:
    """Norma (módulo) de un vector."""
    return math.sqrt(sum(x ** 2 for x in v))

def similitud_coseno(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Similitud de coseno entre dos vectores.
    Retorna un valor entre -1.0 y 1.0.
    1.0 = idénticos, 0.0 = sin relación, -1.0 = opuestos.
    """
    norma_a = _norma(vec_a)
    norma_b = _norma(vec_b)
    if norma_a == 0.0 or norma_b == 0.0:
        return 0.0
    return _dot_product(vec_a, vec_b) / (norma_a * norma_b)

def calcular_semaforo(score: int) -> str:
    """Semáforo completo según la guía del reto."""
    if score >= 76:
        return "Rojo"
    elif score >= 41:
        return "Amarillo"
    return "Verde"

# =====================================================================
# MÓDULO ML — Detección de Anomalías en Montos
#
# Algoritmo: Z-Score sobre el monto reclamado.
# Comparamos el monto del siniestro contra la media y la desviación
# estándar de TODOS los siniestros de la misma cobertura en la BD.
# Un Z-Score alto significa que el monto es estadísticamente atípico.
#
# Puntuación:
#   Z > 3.0  → Muy anómalo  → +15 pts (tope del módulo)
#   Z > 2.0  → Anómalo      → +10 pts
#   Z > 1.5  → Sospechoso   → +5 pts
#   Z ≤ 1.5  → Normal       → +0 pts
# =====================================================================
class ModuloML:

    def _obtener_estadisticas_cobertura(self, tipo_cobertura: str) -> Tuple[float, float, int]:
        """
        Consulta la media y desviación estándar de montos reclamados
        para una cobertura específica.
        Retorna (media, desviacion_std, n_registros).
        """
        response = (
            supabase
            .table("siniestros")
            .select("monto_reclamado, polizas(tipo_cobertura)")
            .execute()
        )

        montos = [
            r["monto_reclamado"]
            for r in response.data
            if r.get("polizas") and r["polizas"].get("tipo_cobertura") == tipo_cobertura
            and r["monto_reclamado"] is not None
        ]

        n = len(montos)
        if n < 2:
            # Sin suficiente historia, no penalizamos
            return 0.0, 0.0, n

        media = sum(montos) / n
        varianza = sum((x - media) ** 2 for x in montos) / (n - 1)  # varianza muestral
        std = math.sqrt(varianza)

        return media, std, n

    def evaluar_monto(self, monto_reclamado: float, tipo_cobertura: str) -> Tuple[int, str]:
        """
        Calcula el Z-Score del monto y retorna (puntos, detalle_log).
        """
        media, std, n = self._obtener_estadisticas_cobertura(tipo_cobertura)

        if n < 2 or std == 0.0:
            return 0, f"Sin historial suficiente para cobertura '{tipo_cobertura}' (n={n})"

        z_score = abs(monto_reclamado - media) / std

        if z_score > 3.0:
            pts = SCORE_MAX_ML  # 15 pts
            nivel = "MUY ANÓMALO"
        elif z_score > 2.0:
            pts = 10
            nivel = "ANÓMALO"
        elif z_score > 1.5:
            pts = 5
            nivel = "SOSPECHOSO"
        else:
            pts = 0
            nivel = "normal"

        detalle = (
            f"Monto ${monto_reclamado:,.2f} | Media ${media:,.2f} | "
            f"σ ${std:,.2f} | Z={z_score:.2f} → {nivel} (+{pts} pts)"
        )
        return pts, detalle


# =====================================================================
# MÓDULO NLP — Detección de Narrativas Clonadas por Similitud de Coseno
#
# Flujo:
#   1. Tomamos el embedding vectorial del siniestro actual (ya guardado
#      en la columna `descripcion_embedding` de Supabase).
#   2. Comparamos contra los embeddings de TODOS los demás siniestros
#      usando similitud de coseno (cálculo local en Python).
#   3. Si algún siniestro supera el umbral del 85%, es narrativa clonada.
#
# Nota sobre la función RPC de Supabase:
#   La guía menciona una función RPC para búsqueda vectorial. Si tienes
#   habilitado pgvector en tu proyecto, puedes reemplazar la comparación
#   local por la llamada RPC (ver método `evaluar_con_rpc` al final).
#   Aquí implementamos la comparación local como fallback universal que
#   funciona sin configuración adicional.
#
# Puntuación:
#   Similitud ≥ 0.85 con ≥3 siniestros  → +15 pts (red organizada)
#   Similitud ≥ 0.85 con 1–2 siniestros → +10 pts (copia probable)
#   Sin coincidencias                    → +0 pts
# =====================================================================
class ModuloNLP:

    def _cargar_embeddings_historicos(
        self, id_siniestro_actual: str
    ) -> List[Dict[str, Any]]:
        """
        Carga los embeddings de todos los siniestros EXCEPTO el actual.
        Solo trae id y embedding para mantener el payload pequeño.
        """
        response = (
            supabase
            .table("siniestros")
            .select("id_siniestro, codigo_siniestro, descripcion_embedding")
            .neq("id_siniestro", id_siniestro_actual)
            .not_.is_("descripcion_embedding", "null")
            .execute()
        )
        return response.data or []

    def evaluar_similitud(
        self,
        id_siniestro_actual: str,
        embedding_actual: List[float],
    ) -> Tuple[int, str, List[str]]:
        """
        Usa la función RPC de Supabase (pgvector) para buscar narrativas similares.
        Más eficiente que la comparación local — delega el cálculo al motor de BD.
        """
        if not embedding_actual:
            return 0, "Sin embedding disponible, NLP omitido.", []

        try:
            response = supabase.rpc("buscar_narrativas_similares", {
                "query_embedding": embedding_actual,
                "match_threshold": UMBRAL_SIMILITUD_NLP,  # 0.85
                "match_count": 10
            }).execute()

            # Excluimos el siniestro actual si aparece en los resultados
            similares = [
                r["codigo_siniestro"]
                for r in (response.data or [])
                if r["id_siniestro"] != id_siniestro_actual
            ]

            n_similares = len(similares)
            max_similitud = max(
                (r["similitud"] for r in (response.data or [])
                if r["id_siniestro"] != id_siniestro_actual),
                default=0.0
            )

            if n_similares >= 3:
                pts = SCORE_MAX_NLP   # 15 pts — red organizada
                nivel = "RED ORGANIZADA"
            elif n_similares >= 1:
                pts = 10              # copia probable
                nivel = "NARRATIVA CLONADA"
            else:
                pts = 0
                nivel = "original"

            detalle = (
                f"pgvector RPC | Similitud máx: {max_similitud:.3f} | "
                f"Coincidencias ≥{UMBRAL_SIMILITUD_NLP:.0%}: {n_similares} → {nivel} (+{pts} pts)"
            )
            return pts, detalle, similares

        except Exception as e:
            # Fallback a comparación local si la RPC falla
            print(f"  RPC falló ({e}), usando comparación local como fallback...")
            return self._evaluar_similitud_local(id_siniestro_actual, embedding_actual)

def _evaluar_similitud_local(
    self,
    id_siniestro_actual: str,
    embedding_actual: List[float],
) -> Tuple[int, str, List[str]]:
    """Fallback: comparación local si pgvector no está disponible."""
    historico = (
        supabase.table("siniestros")
        .select("id_siniestro, codigo_siniestro, descripcion_embedding")
        .neq("id_siniestro", id_siniestro_actual)
        .execute()
    ).data or []

    similares = []
    max_similitud = 0.0

    for registro in historico:
        emb = registro.get("descripcion_embedding")
        if not emb or not isinstance(emb, list):
            continue
        sim = similitud_coseno(embedding_actual, emb)
        if sim > max_similitud:
            max_similitud = sim
        if sim >= UMBRAL_SIMILITUD_NLP:
            similares.append(registro["codigo_siniestro"])

    n = len(similares)
    pts = SCORE_MAX_NLP if n >= 3 else (10 if n >= 1 else 0)
    nivel = "RED ORGANIZADA" if n >= 3 else ("NARRATIVA CLONADA" if n >= 1 else "original")
    detalle = (
        f"Local | Similitud máx: {max_similitud:.3f} | "
        f"Coincidencias: {n} → {nivel} (+{pts} pts)"
    )
    return pts, detalle, similares

def train_model(X, y):
    """Trains the fraud detection model."""
    # En nuestro enfoque usamos Z-Score estadístico, no un modelo entrenado
    # con labels. No necesita "training" en el sentido clásico porque calcula
    # la media y std directamente desde Supabase en tiempo real.
    # Este método existe para cumplir la firma del template.
    # Si en el futuro quieren un modelo supervisado (RandomForest, XGBoost),
    # aquí iría el fit(). Por ahora retornamos None intencionalmente.
    return None


def predict_fraud(X):
    """Returns probability of fraud."""
    # X es un dict con los datos del siniestro. Llamamos al orquestador
    # principal y retornamos el score normalizado como probabilidad (0.0–1.0).
    #
    # Ejemplo de X esperado:
    # {
    #   "id_siniestro": "sin-abc123",
    #   "monto_reclamado": 8500.0,
    #   "tipo_cobertura": "Vehículos Livianos",
    #   "descripcion_embedding": [...],
    #   "score_base": 40   # ya calculado por fraud_rules.py
    # }
    modulo_ml  = ModuloML()
    modulo_nlp = ModuloNLP()

    pts_ml, _  = modulo_ml.evaluar_monto(
        X["monto_reclamado"],
        X.get("tipo_cobertura", "Desconocida")
    )
    pts_nlp, _, _ = modulo_nlp.evaluar_similitud(
        X["id_siniestro"],
        X.get("descripcion_embedding", [])
    )

    score_final = min(X.get("score_base", 0) + pts_ml + pts_nlp, SCORE_MAX_TOTAL)

    # Retornamos probabilidad normalizada (0.0 a 1.0) como pide la firma
    return round(score_final / 100, 4)

# =====================================================================
# ORQUESTADOR DEL PIPELINE DE ML + NLP
# =====================================================================
def procesar_modelos_analiticos():
    print("INICIANDO MÓDULO DE ML + NLP...")

    modulo_ml  = ModuloML()
    modulo_nlp = ModuloNLP()

    # Traemos los siniestros que ya pasaron por el motor de reglas
    # (score_riesgo > 0) pero que aún no tienen score final aplicado.
    # Usamos un campo auxiliar o simplemente re-procesamos todos con
    # score > 0 — el UPDATE es idempotente si ML/NLP suman 0.
    #
    # Para producción real, agregar un campo booleano `ml_procesado`
    # en la tabla siniestros y filtrar por él.
    response = (
        supabase
        .table("siniestros")
        .select("*, polizas(*), proveedores(*)")
        .gt("score_riesgo", 0)
        .execute()
    )

    siniestros = response.data

    if not siniestros:
        print("No hay siniestros pendientes para análisis ML/NLP.")
        return

    print(f" Procesando {len(siniestros)} siniestros...\n")

    for sin in siniestros:
        siniestro_id  = sin["id_siniestro"]
        codigo        = sin["codigo_siniestro"]
        score_base    = sin["score_riesgo"]       # Ya calculado por fraud_rules.py
        embedding     = sin.get("descripcion_embedding") or []
        monto         = sin.get("monto_reclamado") or 0.0
        poliza        = sin.get("polizas") or {}
        tipo_cobertura = poliza.get("tipo_cobertura", "Desconocida")

        print(f"── {codigo} (score base: {score_base}) ──────────────────")

        # --- ML: Anomalía de monto ---
        pts_ml, detalle_ml = modulo_ml.evaluar_monto(monto, tipo_cobertura)
        print(f"  [ML]  {detalle_ml}")

        # --- NLP: Similitud de narrativa ---
        pts_nlp, detalle_nlp, codigos_similares = modulo_nlp.evaluar_similitud(
            siniestro_id, embedding
        )
        print(f"  [NLP] {detalle_nlp}")
        if codigos_similares:
            print(f"        Siniestros similares: {', '.join(codigos_similares[:5])}"
                  + (" ..." if len(codigos_similares) > 5 else ""))

        # --- Consolidación del Score Final ---
        score_final = min(score_base + pts_ml + pts_nlp, SCORE_MAX_TOTAL)
        semaforo_final = calcular_semaforo(score_final)

        print(f"  [SCORE] {score_base} (reglas) + {pts_ml} (ML) + {pts_nlp} (NLP)"
              f" = {score_final}/100 → Semáforo: {semaforo_final}")

        # --- Guardar Score Final en Supabase ---
        try:
            supabase.table("siniestros").update({
                "score_riesgo":   score_final,
                "semaforo_alerta": semaforo_final,
            }).eq("id_siniestro", siniestro_id).execute()
            print(f"  [GUARDADO] ✓\n")
        except Exception as e:
            print(f" Error al guardar {codigo}: {e}\n")


if __name__ == "__main__":
    procesar_modelos_analiticos()
    print("MÓDULO ML + NLP FINALIZADO")
    print("Los siniestros tienen su score definitivo y están listos para el Agente IA.")

