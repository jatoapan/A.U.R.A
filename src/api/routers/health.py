"""
Router de health check
"""
from datetime import datetime
from fastapi import APIRouter, Request

from src.api.schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    GET /health
    Health check y status de modelos
    """
    return HealthResponse(
        status="ok",
        models_loaded=hasattr(request.app.state, "ml_model") and request.app.state.ml_model is not None,
        ml_threshold=request.app.state.ml_config.ml_threshold if hasattr(request.app.state, "ml_config") else 0.7,
        timestamp=datetime.utcnow(),
    )
