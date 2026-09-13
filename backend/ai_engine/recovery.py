import copy
import logging
from typing import Dict, Any
import os
import sys

# Ensure backend can be imported
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from ai_engine.models import (
    RecoverySimulationRequest,
    RecoverySimulationResult,
    RecoveryBeforeAfterState,
    RecoveryDelta,
    AnomalyRequest
)
from ai_engine.anomaly import detect_anomalies
from ai_engine.impact import predict_impact
from ai_engine.rca import analyze_root_cause

# We need baseline configurations to model reasonable recovery targets
from src.config import MACHINES_CONFIG

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {
    "STOP_MAINTAIN": "Immediate Maintenance",
    "DERATE_SPEED": "Reduce Machine Speed",
    "REROUTE_WORKLOAD": "Workload Redistribution",
    "CONTINUE_UNCHECKED": "Ignore Anomaly"
}

def simulate_recovery(request: RecoverySimulationRequest) -> RecoverySimulationResult:
    """
    Simulates the outcome of a recovery action deterministically and safely.
    It does NOT mutate any real machine state.
    """
    assumptions = []
    evidence = []
    
    # 1. Establish Before State
    before = RecoveryBeforeAfterState(
        predicted_telemetry=request.telemetry, # original telemetry
        anomaly_score=request.anomaly.anomaly_score,
        anomaly_severity=request.anomaly.severity,
        production_loss_rate=request.impact.impact.production.loss_rate,
        downtime_risk=request.impact.impact.downtime.risk_score
    )

    # 2. Validate Action
    action_id = request.action.action_id
    if action_id not in SUPPORTED_ACTIONS:
        return _build_invalid_response(request, before, f"Unsupported action: {action_id}. Supported: {list(SUPPORTED_ACTIONS.keys())}")

    machine_id = request.machine_id
    cfg = MACHINES_CONFIG.get(machine_id, {})
    baseline = cfg.get("baseline", {})
    
    # 3. Generate Hypothetical Telemetry
    hypothetical_telemetry = copy.deepcopy(request.telemetry)
    confidence = 1.0
    
    if action_id == "STOP_MAINTAIN":
        # Legacy semantics: "Stop machine now, execute targeted component repair. Causes 30 min stoppage."
        assumptions.append("Simulation assumes STOP_MAINTAIN halts production (throughput=0) and cools machine to baseline.")
        if "throughput" in hypothetical_telemetry:
            hypothetical_telemetry["throughput"] = 0.0
        for key in ["temperature", "vibration", "pressure", "power_consumption"]:
            if key in baseline and key in hypothetical_telemetry:
                hypothetical_telemetry[key] = baseline[key]
                
    elif action_id == "DERATE_SPEED":
        # Simulates reducing speed to 60%, alleviating thermal/vibration stress
        assumptions.append("Simulation assumes DERATE_SPEED caps throughput at 60% baseline and halves deviation of temperature/vibration.")
        if "throughput_uph" in baseline:
            derated_tput = baseline["throughput_uph"] * 0.60
            if "throughput" in hypothetical_telemetry:
                # Throughput might already be lower
                hypothetical_telemetry["throughput"] = min(hypothetical_telemetry["throughput"], derated_tput)
            
        for key in ["temperature", "vibration"]:
            if key in baseline and key in hypothetical_telemetry:
                hypothetical_telemetry[key] = hypothetical_telemetry[key] - 0.50 * (hypothetical_telemetry[key] - baseline[key])
                
    elif action_id == "REROUTE_WORKLOAD":
        # Simulates switching 80% order queue to another line, machine only handles 20%
        assumptions.append("Simulation assumes REROUTE_WORKLOAD drops throughput requirement to 20% baseline, reducing thermal/mechanical stress proportionately (80% reduction).")
        if "throughput_uph" in baseline:
            if "throughput" in hypothetical_telemetry:
                hypothetical_telemetry["throughput"] = baseline["throughput_uph"] * 0.20
        
        for key in ["temperature", "vibration"]:
            if key in baseline and key in hypothetical_telemetry:
                hypothetical_telemetry[key] = hypothetical_telemetry[key] - 0.80 * (hypothetical_telemetry[key] - baseline[key])
                
    elif action_id == "CONTINUE_UNCHECKED":
        assumptions.append("Simulation assumes CONTINUE_UNCHECKED provides no telemetry improvement, leaving machine fully exposed.")
        # Telemetry remains unchanged or could worsen, but we keep it unchanged for stable comparison

    # 4. Re-run Pipelines
    
    # Run Anomaly
    try:
        from ai_engine.models import AnomalyRequest, RCARequest, ImpactRequest
        
        sim_anom_req = AnomalyRequest(machine_id=machine_id, telemetry=hypothetical_telemetry)
        sim_anomaly = detect_anomalies(sim_anom_req)
        
        # Run RCA if still anomalous (otherwise we can use a dummy/healthy RCA)
        if sim_anomaly.is_anomaly:
            sim_rca_req = RCARequest(
                machine_id=machine_id, 
                telemetry=hypothetical_telemetry, 
                anomaly=sim_anomaly, 
                maintenance_history=[] # Keeping history independent
            )
            sim_rca = analyze_root_cause(sim_rca_req)
        else:
            sim_rca = request.rca # we don't necessarily need to rerun RCA if healthy, or we can mock a healthy one
            # To be accurate and deterministic, let's run it.
            sim_rca_req = RCARequest(machine_id=machine_id, telemetry=hypothetical_telemetry, anomaly=sim_anomaly, maintenance_history=[])
            sim_rca = analyze_root_cause(sim_rca_req)
            
        # Run Impact
        sim_impact_req = ImpactRequest(
            machine_id=machine_id,
            telemetry=hypothetical_telemetry,
            anomaly=sim_anomaly,
            rca=sim_rca
        )
        sim_impact = predict_impact(sim_impact_req)
        
    except Exception as e:
        logger.error(f"Recovery simulation pipeline error: {e}")
        return _build_invalid_response(request, before, f"Pipeline execution failed: {str(e)}")

    # 5. Extract After State
    after = RecoveryBeforeAfterState(
        predicted_telemetry=hypothetical_telemetry,
        anomaly_score=sim_anomaly.anomaly_score,
        anomaly_severity=sim_anomaly.severity,
        production_loss_rate=sim_impact.impact.production.loss_rate,
        downtime_risk=sim_impact.impact.downtime.risk_score
    )

    # 6. Calculate Delta
    delta = RecoveryDelta(
        anomaly_score_change=round(after.anomaly_score - before.anomaly_score, 3),
        production_loss_change=round(after.production_loss_rate - before.production_loss_rate, 3) if after.production_loss_rate is not None and before.production_loss_rate is not None else None,
        downtime_risk_change=round(after.downtime_risk - before.downtime_risk, 3),
        throughput_change=round(hypothetical_telemetry.get("throughput", 0.0) - request.telemetry.get("throughput", 0.0), 1) if "throughput" in hypothetical_telemetry and "throughput" in request.telemetry else None
    )

    # 7. Calculate Effectiveness
    # Effectiveness is a score [0.0, 1.0] indicating how much the machine improved.
    # We look at reductions in anomaly score, downtime risk, and production loss rate.
    effectiveness = 0.0
    
    anomaly_improvement = 0.0
    if before.anomaly_score > 0:
        anomaly_improvement = max(0.0, (before.anomaly_score - after.anomaly_score) / before.anomaly_score)
        
    downtime_improvement = 0.0
    if before.downtime_risk > 0:
        downtime_improvement = max(0.0, (before.downtime_risk - after.downtime_risk) / before.downtime_risk)
        
    production_improvement = 0.0
    if before.production_loss_rate is not None and after.production_loss_rate is not None:
        if before.production_loss_rate > 0:
            production_improvement = max(0.0, (before.production_loss_rate - after.production_loss_rate) / before.production_loss_rate)
            # if production drops to 0 throughput, loss rate is 1.0, so improvement will be 0.0 (or negative, floored to 0.0)
        elif after.production_loss_rate == 0:
            production_improvement = 1.0 # it stayed 0
            
    # Combine the three metrics deterministically
    effectiveness = (anomaly_improvement * 0.4) + (downtime_improvement * 0.4) + (production_improvement * 0.2)
        
    # If the machine was already healthy, the effectiveness is ambiguous. 
    if before.anomaly_score == 0 and before.downtime_risk == 0 and (before.production_loss_rate is None or before.production_loss_rate < 0.05):
        effectiveness = 1.0 # It's still healthy
        
    effectiveness = round(max(0.0, min(1.0, effectiveness)), 2)
    
    if effectiveness > 0.8:
        explanation = f"Action '{request.action.name}' highly effective. Substantial reduction in anomaly score and risk."
    elif effectiveness > 0.3:
        explanation = f"Action '{request.action.name}' partially effective. Machine remains in a degraded state."
    else:
        explanation = f"Action '{request.action.name}' ineffective. Negligible improvement in operational state."

    # 8. Adjust Confidence
    # Confidence represents the trustworthiness of the what-if simulation, based on:
    # 1. Baseline availability
    # 2. Telemetry completeness
    # 3. Strength of before-state evidence
    # 4. Action relevance to identified cause
    # 5. Assumption penalties
    
    confidence = 0.0
    
    # 1. Baseline availability (+0.2)
    if cfg:
        confidence += 0.2
    else:
        assumptions.append("Missing machine baseline configuration limits simulation accuracy.")
        
    # 2. Telemetry completeness (+0.2)
    if "throughput" in request.telemetry:
        confidence += 0.2
    else:
        assumptions.append("Missing throughput telemetry limits production loss simulation.")
        
    # 3. Strength of before-state evidence (RCA confidence)
    rca_conf = request.rca.probable_cause.confidence if hasattr(request.rca, "probable_cause") and hasattr(request.rca.probable_cause, "confidence") else getattr(request.rca, "confidence", 0.0)
    if rca_conf >= 0.8:
        confidence += 0.2
    elif rca_conf >= 0.5:
        confidence += 0.1
        
    # 4. Action relevance to identified cause
    fault_type = request.rca.probable_cause.name if hasattr(request.rca, "probable_cause") and hasattr(request.rca.probable_cause, "name") else getattr(request.rca, "fault_type", "NONE")
    relevance_score = 0.0
    
    if action_id == "STOP_MAINTAIN":
        if fault_type != "NONE":
            relevance_score = 0.4 # Highly relevant to any active fault
        else:
            relevance_score = 0.1
    elif action_id == "DERATE_SPEED":
        if "DEGRADATION" in fault_type or "STRESS" in fault_type:
            relevance_score = 0.4
        else:
            relevance_score = 0.1
    elif action_id == "REROUTE_WORKLOAD":
        if "THROUGHPUT" in fault_type or "OVERLOAD" in fault_type:
            relevance_score = 0.4
        else:
            relevance_score = 0.1
    elif action_id == "CONTINUE_UNCHECKED":
        relevance_score = 0.4 # We are highly confident in our ability to simulate 'doing nothing'
        
    confidence += relevance_score
    
    # 5. Assumption Penalty
    # Acknowledge that explicitly manipulating physical traits is an assumption.
    if action_id in ["STOP_MAINTAIN", "DERATE_SPEED", "REROUTE_WORKLOAD"]:
        confidence -= 0.1
        
    confidence = round(max(0.0, min(1.0, confidence)), 2)

    return RecoverySimulationResult(
        machine_id=machine_id,
        action=request.action,
        before=before,
        after=after,
        delta=delta,
        recovery_effectiveness=effectiveness,
        confidence=confidence,
        assumptions=assumptions,
        evidence=[
            f"Anomaly score change: {delta.anomaly_score_change}",
            f"Downtime risk change: {delta.downtime_risk_change}"
        ],
        explanation=explanation
    )

def _build_invalid_response(request: RecoverySimulationRequest, before: RecoveryBeforeAfterState, message: str) -> RecoverySimulationResult:
    # Safe fallback for invalid actions
    after = RecoveryBeforeAfterState(
        predicted_telemetry=request.telemetry,
        anomaly_score=before.anomaly_score,
        anomaly_severity=before.anomaly_severity,
        production_loss_rate=before.production_loss_rate,
        downtime_risk=before.downtime_risk
    )
    delta = RecoveryDelta(
        anomaly_score_change=0.0,
        production_loss_change=0.0,
        downtime_risk_change=0.0,
        throughput_change=0.0
    )
    return RecoverySimulationResult(
        machine_id=request.machine_id,
        action=request.action,
        before=before,
        after=after,
        delta=delta,
        recovery_effectiveness=0.0,
        confidence=0.0,
        assumptions=[message],
        evidence=[],
        explanation="Simulation unavailable for this action because no defensible recovery model exists."
    )
