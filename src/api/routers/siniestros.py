"""
Router de siniestros - endpoints principales
"""
from datetime import datetime
from typing import Optional
import logging
import traceback

from fastapi import APIRouter, HTTPException, Depends, Request

from src.api.schemas import (
    SiniestroListResponse,
    SiniestroDetalle,
    ScoreResponse,
    BatchScoreResponse,
)
from src.api.deps import get_supabase_client
from src.api.services import SupabaseRepository
from src.api.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


router = APIRouter()


def get_repo(client=Depends(get_supabase_client)):
    """Obtener repositorio Supabase"""
    return SupabaseRepository(client)


def get_scoring_service(request: Request, repo=Depends(get_repo)):
    """Obtener servicio de scoring con modelos del app state"""
    logger.info("🔵 [DEP] get_scoring_service() iniciado")
    
    try:
        logger.info(f"🔵 [DEP] Verificando app.state...")
        logger.info(f"🔵 [DEP] app.state attributes: {dir(request.app.state)}")
        
        if not hasattr(request.app.state, "ml_model"):
            logger.error("❌ [DEP] ml_model no encontrado en app.state")
            raise HTTPException(status_code=500, detail="Modelos no cargados. Ejecuta: python scripts/train_fraud_model.py")
        
        logger.info(f"🔵 [DEP] ml_model type: {type(request.app.state.ml_model)}")
        
        if not hasattr(request.app.state, "anomaly_model"):
            logger.error("❌ [DEP] anomaly_model no encontrado en app.state")
            raise HTTPException(status_code=500, detail="Modelo de anomalías no cargado")
        
        logger.info(f"🔵 [DEP] anomaly_model type: {type(request.app.state.anomaly_model)}")
        
        if not hasattr(request.app.state, "ml_config"):
            logger.error("❌ [DEP] ml_config no encontrado en app.state")
            raise HTTPException(status_code=500, detail="Configuración ML no cargada")
        
        logger.info(f"🔵 [DEP] ml_config type: {type(request.app.state.ml_config)}")
        
        service = ScoringService(
            ml_model=request.app.state.ml_model,
            anomaly_model=request.app.state.anomaly_model,
            ml_config=request.app.state.ml_config,
        )
        logger.info("✅ [DEP] ScoringService creado exitosamente")
        return service
        
    except HTTPException:
        logger.error("❌ [DEP] HTTPException lanzada")
        raise
    except Exception as e:
        logger.error(f"❌ [DEP] Error inesperado: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en get_scoring_service: {str(e)}")


# ==================== GET ====================

@router.get("", response_model=SiniestroListResponse)
async def list_siniestros(
    semaforo: Optional[str] = None,
    min_score: Optional[int] = None,
    cobertura: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort: str = "score_riesgo_desc",
    repo: SupabaseRepository = Depends(get_repo),
) -> SiniestroListResponse:
    """
    GET /siniestros
    Listar siniestros con filtros opcionales
    
    Parámetros:
    - semaforo: VERDE, AMARILLO, ROJO
    - min_score: score mínimo (0-100)
    - cobertura: CHOQUE, ROBO, DAÑOS
    - limit: items por página
    - offset: página (limit × offset)
    """
    try:
        result = repo.list_siniestros(
            semaforo=semaforo,
            min_score=min_score,
            cobertura=cobertura,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return SiniestroListResponse(
            total=result["total"],
            items=[SiniestroDetalle(**item) for item in result["items"]],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id_siniestro}", response_model=SiniestroDetalle)
async def get_siniestro(
    id_siniestro: str,
    repo: SupabaseRepository = Depends(get_repo),
) -> SiniestroDetalle:
    """
    GET /siniestros/{id_siniestro}
    Obtener detalle completo de un siniestro
    """
    try:
        siniestro = repo.fetch_siniestro(id_siniestro)
        if not siniestro:
            raise HTTPException(status_code=404, detail=f"Siniestro no encontrado: {id_siniestro}")
        
        return SiniestroDetalle(**siniestro)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== POST - SCORE ====================

@router.post("/{id_siniestro}/score", response_model=ScoreResponse)
async def score_siniestro(
    id_siniestro: str,
    request: Request,
    repo: SupabaseRepository = Depends(get_repo),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> ScoreResponse:
    """
    POST /siniestros/{id_siniestro}/score
    Calcular score de riesgo y guardar en BD
    """
    try:
        logger.info(f"🔵 [SCORE] Iniciando para: {id_siniestro}")
        
        # Obtener tablas necesarias para scoring
        logger.info(f"🔵 [SCORE] Obteniendo tablas...")
        tables = repo.fetch_scoring_tables(id_siniestro)
        logger.info(f"✅ [SCORE] Tablas obtenidas: {list(tables.keys())}")
        
        if tables["siniestros"].empty:
            logger.error(f"❌ [SCORE] Siniestro vacío: {id_siniestro}")
            raise HTTPException(status_code=404, detail=f"Siniestro no encontrado: {id_siniestro}")
        
        logger.info(f"🔵 [SCORE] Calculando score...")
        # Calcular score
        result = scoring_service.score_one_claim(tables, id_siniestro)
        logger.info(f"✅ [SCORE] Score calculado: {result}")
        
        logger.info(f"🔵 [SCORE] Guardando en BD...")
        # Guardar en Supabase
        repo.persist_score(id_siniestro, result)
        logger.info(f"✅ [SCORE] Guardado en BD")
        
        logger.info(f"🔵 [SCORE] Construyendo respuesta...")
        # Retornar respuesta
        response = ScoreResponse(
            id_siniestro=id_siniestro,
            score_final=int(result["score_final"]),
            semaforo=str(result["semaforo"]),
            explicacion=str(result["explicacion"]),
            score_reglas=int(result["score_reglas"]),
            ml_proba=float(result["ml_proba"]),
            ml_alerta=int(result["ml_alerta"]),
            anom_score_0_1=float(result.get("anom_score_0_1", 0)),
            timestamp=datetime.utcnow(),
        )
        logger.info(f"✅ [SCORE] Respuesta construida exitosamente")
        return response
        
    except HTTPException:
        logger.error(f"❌ [SCORE] HTTPException")
        raise
    except Exception as e:
        logger.error(f"❌ [SCORE] Error inesperado: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error scoring: {str(e)}")


@router.post("/score-all", response_model=BatchScoreResponse)
async def score_all_siniestros(
    request: Request,
    repo: SupabaseRepository = Depends(get_repo),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> BatchScoreResponse:
    """
    POST /siniestros/score-all
    Recalcular scores para TODOS los siniestros (puede tardar)
    """
    try:
        logger.info("🔵 [BATCH SCORE] Iniciando scoring batch...")
        
        # Obtener todas las tablas
        logger.info("🔵 [BATCH SCORE] Obteniendo tablas de Supabase...")
        tables = repo.fetch_scoring_tables()
        logger.info(f"✅ [BATCH SCORE] Tablas obtenidas: {list(tables.keys())}")
        
        # Verificar que hay datos
        if tables.get("siniestros", None) is None or tables["siniestros"].empty:
            logger.warning("⚠️  [BATCH SCORE] No hay siniestros en BD")
            raise ValueError("No hay siniestros para procesar")
        
        logger.info(f"✅ [BATCH SCORE] {len(tables['siniestros'])} siniestros encontrados")
        
        # Scoring batch
        logger.info("🔵 [BATCH SCORE] Ejecutando scoring...")
        scored_df = scoring_service.score_batch(tables)
        logger.info(f"✅ [BATCH SCORE] Scoring completado: {len(scored_df)} filas procesadas")
        
        # Verificar resultados
        if scored_df.empty:
            logger.warning("⚠️  [BATCH SCORE] DataFrame vacío después de scoring")
            raise ValueError("Scoring resultó en dataframe vacío")
        
        # Verificar que hay columnas esperadas
        expected_cols = ["score_final", "semaforo", "ml_proba", "score_reglas"]
        missing_cols = [c for c in expected_cols if c not in scored_df.columns]
        if missing_cols:
            logger.error(f"❌ [BATCH SCORE] Columnas faltantes: {missing_cols}")
            logger.error(f"Columnas disponibles: {scored_df.columns.tolist()}")
            raise ValueError(f"Columnas faltantes en scoring: {missing_cols}")
        
        logger.info(f"✅ [BATCH SCORE] Columnas OK: score_final, semaforo, ml_proba, score_reglas")
        
        # Persistir todos
        logger.info("🔵 [BATCH SCORE] Persistiendo scores en BD...")
        count = repo.batch_persist_scores(scored_df)
        logger.info(f"✅ [BATCH SCORE] {count} registros actualizados en BD")
        
        # Contar por semáforo
        logger.info("🔵 [BATCH SCORE] Calculando distribución de semáforos...")
        semaforo_counts = scoring_service.get_semaforo_counts(tables)
        logger.info(f"✅ [BATCH SCORE] Distribución: {semaforo_counts}")
        
        logger.info("✅ [BATCH SCORE] Completado exitosamente")
        
        return BatchScoreResponse(
            processed=count,
            semaforo_counts=semaforo_counts,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        import traceback
        logger.error(f"❌ [BATCH SCORE] Error: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in batch scoring: {str(e)}")
