import os
from typing import Dict, Any, List
from dateutil import parser
from dotenv import load_dotenv
from supabase import create_client, Client

# =====================================================================
# CONFIGURACIÓN — Credenciales desde variables de entorno (.env)
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
# El motor de reglas aporta hasta 70 puntos.
# El Modelo ML y el NLP aportarán los 30 puntos restantes (hasta llegar a 100).
# =====================================================================
SCORE_MAX_REGLAS: int = 70

# =====================================================================
# MOTOR DE REGLAS DE NEGOCIO (RF-01 a RF-07 + Nuevas)
# =====================================================================
class ReglasNegocioEngine:

    def evaluar_borde_vigencia(self, fecha_inicio_poliza: str, fecha_siniestro: str) -> int:
        """RF-01: Penaliza si el siniestro ocurre muy cerca de la contratación de la póliza."""
        dt_poliza = parser.isoparse(fecha_inicio_poliza)
        dt_siniestro = parser.isoparse(fecha_siniestro)
        diferencia_horas = (dt_siniestro - dt_poliza).total_seconds() / 3600

        if diferencia_horas < 24:
            return 40   # Riesgo Crítico
        elif diferencia_horas < 72:
            return 20   # Riesgo Moderado
        return 0

    def evaluar_demora_notificacion(self, fecha_siniestro: str, fecha_notificacion: str) -> int:
        """RF-04: Penaliza si el cliente tarda demasiado en avisar a la aseguradora."""
        dt_siniestro = parser.isoparse(fecha_siniestro)
        dt_notif = parser.isoparse(fecha_notificacion)
        diferencia_dias = (dt_notif - dt_siniestro).days

        if diferencia_dias > 10:
            return 30   # Riesgo Alto
        elif diferencia_dias > 5:
            return 15   # Riesgo Medio
        return 0

    def evaluar_proveedor(self, proveedor: Dict[str, Any]) -> int:
        """RF-03: Penaliza si el taller o perito está en lista restrictiva."""
        if not proveedor:
            return 0
        if proveedor.get('lista_restrictiva', False):
            return 50   # Riesgo Crítico Directo
        return 0

    def evaluar_documentos(self, documentos: List[Dict[str, Any]]) -> int:
        """RF-06 y RF-07: Analiza metadatos de documentos adjuntos."""
        score_doc = 0
        if not documentos:
            return score_doc

        for doc in documentos:
            if doc.get('posible_adulteracion', False):
                score_doc += 35   # Documento falso o adulterado
            elif not doc.get('es_legible', True):
                score_doc += 10   # Documento borroso (táctica común)

        return min(score_doc, 40)  # Tope por documentos: 40 pts

    def evaluar_historial_siniestros(self, historial: int) -> int:
        """RF-Nueva: Penaliza si el asegurado tiene un historial frecuente de siniestros."""
        if historial >= 3:
            return 25   # Alta reincidencia
        elif historial == 2:
            return 10   # Reincidencia moderada
        return 0

    def evaluar_documentacion_incompleta(self, completos: bool) -> int:
        """RF-Nueva: Penaliza (levemente) si el trámite se intenta procesar sin documentos completos."""
        if not completos:
            return 15   # Trámite inusual o apresurado
        return 0


# =====================================================================
# SEMÁFORO — Función centralizada para asignar nivel de alerta
# Escala completa según la guía del reto:
#   Verde    → 0–40
#   Amarillo → 41–75
#   Rojo     → 76–100
# =====================================================================
def calcular_semaforo(score: int) -> str:
    if score >= 76:
        return "Rojo"
    elif score >= 41:
        return "Amarillo"
    return "Verde"


# =====================================================================
# ORQUESTADOR DEL PIPELINE
# =====================================================================
def procesar_siniestros_nuevos():
    print("INICIANDO MOTOR DE REGLAS DE NEGOCIO...")
    engine = ReglasNegocioEngine()

    # 1. Obtener siniestros pendientes de evaluación (score = 0)
    response = supabase.table("siniestros").select(
        "*, polizas(*), proveedores(*), documentos(*)"
    ).eq("score_riesgo", 0).execute()

    siniestros = response.data

    if not siniestros:
        print("No hay siniestros nuevos para evaluar.")
        return

    print(f"Evaluando {len(siniestros)} siniestros pendientes...\n")

    for sin in siniestros:
        siniestro_id = sin['id_siniestro']
        codigo = sin['codigo_siniestro']
        score_acumulado = 0
        alertas = []

        print(f"Analizando {codigo}...")

        # --- Regla RF-01: Borde de Vigencia ---
        poliza = sin.get('polizas')
        if poliza and poliza.get('fecha_inicio_vigencia'):
            pts_vigencia = engine.evaluar_borde_vigencia(
                poliza['fecha_inicio_vigencia'],
                sin['fecha_siniestro']
            )
            if pts_vigencia > 0:
                alertas.append(f"  → Alerta Vigencia (+{pts_vigencia} pts)")
            score_acumulado += pts_vigencia
        else:
            print(f" {codigo}: no se encontró póliza vinculada, se omite RF-01.")

        # --- Regla RF-04: Demora en Notificación ---
        pts_demora = engine.evaluar_demora_notificacion(
            sin['fecha_siniestro'],
            sin['fecha_notificacion']
        )
        if pts_demora > 0:
            alertas.append(f"  → Alerta Demora (+{pts_demora} pts)")
        score_acumulado += pts_demora

        # --- Regla RF-03: Proveedor en Lista Restrictiva ---
        pts_proveedor = engine.evaluar_proveedor(sin.get('proveedores') or {})
        if pts_proveedor > 0:
            alertas.append(f"  → Alerta Proveedor ({sin.get('proveedores', {}).get('nombre_comercial', 'N/D')}) (+{pts_proveedor} pts)")
        score_acumulado += pts_proveedor

        # --- Reglas RF-06 y RF-07: Documentos ---
        pts_docs = engine.evaluar_documentos(sin.get('documentos') or [])
        if pts_docs > 0:
            alertas.append(f"  → Alerta Documentos (+{pts_docs} pts)")
        score_acumulado += pts_docs

        # --- Nueva Regla: Historial de Asegurado ---
        pts_historial = engine.evaluar_historial_siniestros(sin.get('historial_siniestros_asegurado', 0))
        if pts_historial > 0:
            alertas.append(f"  → Alerta Historial ({sin.get('historial_siniestros_asegurado')} previos) (+{pts_historial} pts)")
        score_acumulado += pts_historial

        # --- Nueva Regla: Documentación Incompleta ---
        # Usamos True como default por si el campo viene nulo, asumiendo buena fe inicial
        pts_docs_completos = engine.evaluar_documentacion_incompleta(sin.get('documentos_completos', True))
        if pts_docs_completos > 0:
            alertas.append(f"  → Alerta Docs Incompletos (+{pts_docs_completos} pts)")
        score_acumulado += pts_docs_completos

        # 2. Aplicar tope del módulo de reglas para dejar espacio al ML y NLP.
        score_acumulado = min(score_acumulado, SCORE_MAX_REGLAS)

        # 3. Semáforo con tres niveles completos (Verde / Amarillo / Rojo).
        semaforo = calcular_semaforo(score_acumulado)

        # Imprimir resumen del caso
        if alertas:
            for alerta in alertas:
                print(alerta)
        else:
            print("  → Sin alertas detectadas por reglas.")

        # 4. Guardar resultado en Supabase
        try:
            supabase.table("siniestros").update({
                "score_riesgo": score_acumulado,
                "semaforo_alerta": semaforo
            }).eq("id_siniestro", siniestro_id).execute()
            print(f"  [GUARDADO] Score Base: {score_acumulado}/70 | Semáforo: {semaforo}\n")
        except Exception as e:
            print(f" Error al guardar {codigo}: {e}\n")


if __name__ == "__main__":
    procesar_siniestros_nuevos()
    print("MOTOR DE REGLAS FINALIZADO")
    print("Los siniestros están listos para el Modelo de Machine Learning y NLP.")