"""
Router de chat - agente LLM conversacional con OpenAI
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request

from src.api.schemas import ChatRequest, ChatResponse
from src.api.deps import get_supabase_client
from src.api.services import SupabaseRepository
from src.agents.claims_agent import run_claims_agent

logger = logging.getLogger(__name__)

router = APIRouter()


def get_repo(client=Depends(get_supabase_client)):
    """Obtener repositorio"""
    return SupabaseRepository(client)


def build_context_for_agent(siniestro_data: dict) -> dict:
    """
    Construir contexto del siniestro para enviar al agente OpenAI
    
    Args:
        siniestro_data: datos del siniestro desde BD
    
    Returns:
        dict con campos necesarios para el prompt del agente
    """
    return {
        "codigo_siniestro": siniestro_data.get("codigo_siniestro", "N/A"),
        "score_riesgo": siniestro_data.get("score_riesgo", 0),
        "semaforo_alerta": siniestro_data.get("semaforo_alerta", "VERDE"),
        "explicacion": siniestro_data.get("explicacion_riesgo") or siniestro_data.get("explicacion", "Sin explicación"),
        "cobertura": siniestro_data.get("cobertura", "N/A"),
        "monto_reclamado": siniestro_data.get("monto_reclamado", 0),
        "descripcion_narrativa": siniestro_data.get("descripcion_narrativa", "Sin narrativa"),
        "score_reglas": siniestro_data.get("score_reglas", 0),
        "ml_proba": siniestro_data.get("ml_proba", 0),
        "anom_score": siniestro_data.get("anom_score_0_1") or siniestro_data.get("anom_score", 0),
    }


@router.post("/{id_siniestro}/chat", response_model=ChatResponse)
async def chat(
    id_siniestro: str,
    chat_request: ChatRequest,
    repo: SupabaseRepository = Depends(get_repo),
) -> ChatResponse:
    """
    POST /siniestros/{id_siniestro}/chat
    Chat conversacional con agente OpenAI que explica el siniestro
    """
    try:
        logger.info(f"🔵 [CHAT] Iniciando para siniestro: {id_siniestro}")
        logger.info(f"🔵 [CHAT] Mensajes recibidos: {len(chat_request.messages)}")
        
        # Obtener siniestro de BD
        logger.info(f"🔵 [CHAT] Buscando siniestro en BD...")
        siniestro = repo.fetch_siniestro(id_siniestro)
        if not siniestro:
            logger.warning(f"⚠️  [CHAT] Siniestro no encontrado: {id_siniestro}")
            raise HTTPException(status_code=404, detail=f"Siniestro no encontrado: {id_siniestro}")
        
        logger.info(f"✅ [CHAT] Siniestro encontrado")
        
        # Validar que siniestro sea un dict
        if isinstance(siniestro, str):
            logger.warning(f"⚠️  [CHAT] Siniestro es string, no dict")
            siniestro = {}
        
        # Construir contexto para agente
        logger.info(f"🔵 [CHAT] Construyendo contexto...")
        context = build_context_for_agent(siniestro)
        logger.info(f"✅ [CHAT] Contexto construido: score={context.get('score_riesgo')}")
        
        # Convertir mensajes a formato compatible
        logger.info(f"🔵 [CHAT] Procesando mensajes...")
        messages = []
        for msg in chat_request.messages:
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        logger.info(f"✅ [CHAT] Mensajes procesados: {len(messages)} válidos")
        
        # Validar que hay al menos un mensaje
        if not messages:
            logger.error(f"❌ [CHAT] No hay mensajes válidos")
            raise ValueError("No hay mensajes en la solicitud")
        
        # Llamar agente OpenAI con contexto y mensajes del usuario
        logger.info(f"🔵 [CHAT] Llamando OpenAI agent...")
        reply = run_claims_agent(
            messages=messages,
            context=context
        )
        logger.info(f"✅ [CHAT] Respuesta recibida: {len(reply)} caracteres")
        
        return ChatResponse(
            id_siniestro=id_siniestro,
            reply=reply,
            sources=["score_riesgo", "ml_proba", "score_reglas", "explicacion_riesgo"],
            timestamp=datetime.utcnow(),
        )
    
    except HTTPException:
        logger.error(f"❌ [CHAT] HTTPException")
        raise
    except ValueError as e:
        logger.error(f"❌ [CHAT] ValueError: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error de configuración: {str(e)}"
        )
    except Exception as e:
        import traceback
        logger.error(f"❌ [CHAT] Exception: {str(e)}")
        traceback.print_exc()
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")
