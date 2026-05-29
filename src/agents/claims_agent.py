"""
Claims Agent - Agente conversacional con OpenAI para análisis de siniestros
Integración: OpenAI GPT para explicar decisiones de scoring
"""
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Cargar .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class ClaimsAgent:
    """Agente de análisis de siniestros con OpenAI"""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY no está configurada en .env\n"
                "Obtener desde: https://platform.openai.com/api-keys"
            )
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # gpt-4 requiere acceso específico; gpt-3.5-turbo es rápido y confiable
    
    def build_system_prompt(self, context: Dict) -> str:
        """Construir prompt del sistema con contexto del siniestro"""
        return f"""Eres A.U.R.A, asistente de analistas de siniestros de Aseguradora del Sur.

Tu rol:
✓ Explicar indicadores de riesgo detectados
✓ Responder preguntas sobre el caso
✓ Ser breve y profesional
✗ NO reemplazar decisiones del scoring automático
✗ NO afirmar fraude confirmado - usar "señales de riesgo" o "indicadores"

CONTEXTO DEL CASO ACTUAL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Código: {context.get('codigo_siniestro', 'N/A')}
Score de Riesgo: {context.get('score_riesgo', 'N/A')}/100
Semáforo: {context.get('semaforo_alerta', 'N/A')}
Cobertura: {context.get('cobertura', 'N/A')}
Monto Reclamado: ${context.get('monto_reclamado', 'N/A')}

ANÁLISIS DETALLADO:
• Puntuación por Reglas: {context.get('score_reglas', 'N/A')}/70
• Probabilidad ML: {context.get('ml_proba', 'N/A')}
• Score Anomalías: {context.get('anom_score', 'N/A')}/10

Explicación del Score: {context.get('explicacion', 'N/A')}

NARRATIVA DEL EVENTO:
{context.get('descripcion_narrativa', 'Sin información')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usa SOLO este contexto para responder. Si no hay información, dilo claramente.
Responde en español, de forma profesional y concisa."""
    
    def run(self, messages: List[Dict], context: Dict) -> str:
        """
        Ejecutar agente con historial de mensajes
        
        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            context: dict con score, explicación, narrativa, etc
        
        Returns:
            str: respuesta del agente
        """
        try:
            # Validar contexto
            if not context or not isinstance(context, dict):
                return "Error: Contexto del siniestro no disponible"
            
            system_prompt = self.build_system_prompt(context)
            
            # Validar mensajes
            if not messages or len(messages) == 0:
                return "Error: No hay mensajes para procesar"
            
            # Filtrar mensajes válidos
            valid_messages = [
                m for m in messages 
                if isinstance(m, dict) and m.get("content")
            ]
            
            if not valid_messages:
                return "Error: Mensajes inválidos"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *valid_messages,  # Historial del usuario
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            return response.choices[0].message.content
        
        except ValueError as e:
            return f"Error de configuración: {str(e)}"
        except Exception as e:
            import traceback
            
            error_msg = str(e)
            traceback.print_exc()
            
            # Si es problema de quota/billing en OpenAI, usar fallback
            if "429" in error_msg or "insufficient_quota" in error_msg:
                logger.warning(f"⚠️  [AGENT] OpenAI quota excedida - usando respuesta fallback")
                return self._generate_fallback_response(context)
            
            return f"Error al procesar consulta: {error_msg}"
    
    def _generate_fallback_response(self, context: Dict) -> str:
        """
        Genera respuesta simulada cuando OpenAI no está disponible
        (Útil para testing de UI sin crédito OpenAI)
        """
        score = context.get("score_riesgo", 0)
        semaforo = context.get("semaforo_alerta", "DESCONOCIDO")
        cobertura = context.get("cobertura", "N/A")
        
        templates = {
            "ROJO": f"""🔴 **ALERTA CRÍTICA - Score {score}/100**

Este siniestro presenta múltiples indicadores de riesgo:
• Score elevado ({score}) en escala de 0-100
• Clasificación: ROJO (requiere revisión urgente)
• Cobertura: {cobertura}

Recomendación: Requiere investigación inmediata del área de fraude.""",
            
            "AMARILLO": f"""🟡 **REVISIÓN RECOMENDADA - Score {score}/100**

Este caso presenta señales de riesgo moderadas:
• Score intermedio ({score}) indica necesidad de verificación
• Clasificación: AMARILLO (análisis adicional sugerido)
• Cobertura: {cobertura}

Recomendación: Verificar documentación antes de autorizar.""",
            
            "VERDE": f"""🟢 **BAJO RIESGO - Score {score}/100**

Este siniestro parece dentro de parámetros normales:
• Score aceptable ({score}) en evaluación automática
• Clasificación: VERDE (perfil compatible)
• Cobertura: {cobertura}

Recomendación: Procede según política estándar.""",
        }
        
        return templates.get(semaforo, f"Score: {score}/100 - Semáforo: {semaforo}")


# Instancia global
_agent: Optional[ClaimsAgent] = None


def get_agent() -> ClaimsAgent:
    """Obtener instancia singleton del agente"""
    global _agent
    if _agent is None:
        _agent = ClaimsAgent()
    return _agent


def run_claims_agent(messages: List[Dict], context: Dict) -> str:
    """
    Función pública para ejecutar el agente
    
    Usage:
        reply = run_claims_agent(
            messages=[{"role": "user", "content": "¿Por qué alto riesgo?"}],
            context={"score_riesgo": 68, "semaforo_alerta": "AMARILLO", ...}
        )
    """
    agent = get_agent()
    return agent.run(messages, context)

