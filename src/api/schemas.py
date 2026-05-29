"""
Esquemas Pydantic para request/response de A.U.R.A API
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ==================== Siniestro ====================

class SiniestroBase(BaseModel):
    """Base de siniestro"""
    codigo_siniestro: str
    cobertura: str
    sucursal: str
    monto_reclamado: float
    descripcion_narrativa: Optional[str] = None
    estado_tramite: Optional[str] = "EN REVISION"


class SiniestroCreate(SiniestroBase):
    """Para crear siniestro"""
    pass


class SiniestroDetalle(SiniestroBase):
    """Detalle completo de siniestro con score"""
    id_siniestro: str
    monto_estimado: Optional[float] = None
    score_riesgo: int = Field(default=0, ge=0, le=100)
    semaforo_alerta: str = Field(default="VERDE")
    score_reglas: Optional[int] = None
    ml_proba: Optional[float] = None
    ml_alerta: Optional[int] = None
    anom_score_0_1: Optional[float] = None
    explicacion_riesgo: Optional[str] = None
    explicacion: Optional[str] = None
    fecha_reporte: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SiniestroListResponse(BaseModel):
    """Respuesta para listado de siniestros"""
    total: int
    items: List[SiniestroDetalle]


# ==================== Score ====================

class ScoreRequest(BaseModel):
    """Request para recalcular score"""
    recalculate: bool = True


class ScoreResponse(BaseModel):
    """Respuesta después de calcular score"""
    id_siniestro: str
    score_final: int = Field(ge=0, le=100)
    semaforo: str
    explicacion: str
    score_reglas: int
    ml_proba: float
    ml_alerta: int
    anom_score_0_1: float
    timestamp: datetime


# ==================== Chat ====================

class ChatMessage(BaseModel):
    """Un mensaje en la conversación"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request para chat"""
    messages: List[ChatMessage]
    # Nota: id_siniestro viene en la URL, no en el body


class ChatResponse(BaseModel):
    """Respuesta del chat"""
    id_siniestro: str
    reply: str
    sources: List[str] = []
    timestamp: datetime


# ==================== Health ====================

class HealthResponse(BaseModel):
    """Status de la API"""
    status: str
    models_loaded: bool
    ml_threshold: float = 0.7
    timestamp: datetime


# ==================== Batch Scoring ====================

class BatchScoreResponse(BaseModel):
    """Respuesta de scoring batch"""
    processed: int
    semaforo_counts: dict
    timestamp: datetime
