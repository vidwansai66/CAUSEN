from fastapi import APIRouter, HTTPException
import logging
from .models import (
    AnomalyRequest, 
    AnomalyResult,
    RCARequest,
    RCAResult,
    ImpactRequest,
    ImpactResult,
    RecoverySimulationRequest,
    RecoverySimulationResult,
    DecisionRequest,
    DecisionResult
)
from .anomaly import detect_anomalies
from .rca import analyze_root_cause
from .impact import predict_impact
from .recovery import simulate_recovery
from .decision import make_decision

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])

@router.post("/anomaly", response_model=AnomalyResult)
def evaluate_anomaly(request: AnomalyRequest):
    try:
        return detect_anomalies(request)
    except Exception as e:
        logger.error(f"Anomaly evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rca", response_model=RCAResult)
def evaluate_rca(request: RCARequest):
    try:
        return analyze_root_cause(request)
    except Exception as e:
        logger.error(f"RCA evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/impact", response_model=ImpactResult)
def evaluate_impact(request: ImpactRequest):
    try:
        return predict_impact(request)
    except Exception as e:
        logger.error(f"Impact prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recovery/simulate", response_model=RecoverySimulationResult)
def evaluate_recovery(request: RecoverySimulationRequest):
    try:
        return simulate_recovery(request)
    except Exception as e:
        logger.error(f"Recovery simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decision", response_model=DecisionResult)
def evaluate_decision(request: DecisionRequest):
    try:
        return make_decision(request)
    except Exception as e:
        logger.error(f"Decision engine failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from .models import PipelineRequest, PipelineResult
from .orchestrator import run_ai_pipeline

@router.post("/analyze", response_model=PipelineResult)
def analyze_full_pipeline(request: PipelineRequest):
    try:
        if not request.telemetry:
            raise ValueError("telemetry data is required")
        return run_ai_pipeline(request)
    except Exception as e:
        logger.error(f"Full pipeline analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
