"""
FastAPI App - A.U.R.A Fraud Detection System
Integración con Supabase + Motor de scoring híbrido (Reglas + ML + Anomalías + NLP)
"""
from contextlib import asynccontextmanager
from pathlib import Path
import sys
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.anomaly_model import load_anomaly_model
from src.models.fraud_model import load_model, load_model_config
from src.api.routers import health, siniestros, chat

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle de FastAPI:
    - startup: cargar modelos en memoria
    - shutdown: limpiar recursos
    """
    # ==================== STARTUP ====================
    logger.info("🚀 Cargando modelos ML...")
    try:
        app.state.ml_model = load_model()
        logger.info("✓ Modelo fraud (LogisticRegression) cargado")
    except Exception as e:
        logger.error(f"✗ Error cargando fraud model: {e}")
        app.state.ml_model = None

    try:
        app.state.anomaly_model = load_anomaly_model()
        logger.info("✓ Modelo anomalías (IsolationForest) cargado")
    except Exception as e:
        logger.error(f"✗ Error cargando anomaly model: {e}")
        app.state.anomaly_model = None

    try:
        app.state.ml_config = load_model_config()
        logger.info(f"✓ Configuración ML cargada (threshold={app.state.ml_config.ml_threshold})")
    except Exception as e:
        logger.error(f"✗ Error cargando config: {e}")
        app.state.ml_config = None

    if app.state.ml_model and app.state.anomaly_model:
        logger.info("✅ Sistema listo para scoring")
    else:
        logger.warning("⚠️  Modelos incompletos - ejecuta: python scripts/train_fraud_model.py")

    yield

    # ==================== SHUTDOWN ====================
    logger.info("🛑 Apagando la aplicación...")


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para loguear TODOS los errores 500 con traceback completo"""
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"❌ ERROR 500 - {request.method} {request.url.path}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal server error: {str(e)}", "type": type(e).__name__}
            )


# Crear app
app = FastAPI(
    title="A.U.R.A API",
    description="Sistema de detección de fraude en siniestros - Aseguradora del Sur",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod: restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error logging middleware
app.add_middleware(ErrorLoggingMiddleware)

# Routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(siniestros.router, prefix="/siniestros", tags=["siniestros"])
app.include_router(chat.router, prefix="/siniestros", tags=["chat"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to A.U.R.A Fraud Detection API",
        "docs": "/docs",
        "health": "/health",
    }

