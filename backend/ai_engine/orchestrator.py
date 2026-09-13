from typing import Dict, Any

# pyrefly: ignore [missing-import]
from .models import (
    PipelineRequest,
    PipelineResult,
    AnomalyRequest,
    RCARequest,
    ImpactRequest,
    RecoverySimulationRequest,
    RecoveryAction
)
from .anomaly import detect_anomalies
from .rca import analyze_root_cause
from .impact import predict_impact
from .recovery import simulate_recovery
from .decision import make_decision

def run_ai_pipeline(request: PipelineRequest) -> PipelineResult:
    """
    Executes the full deterministic AI pipeline (Parts 1-7).
    """
    machine_id = request.machine_id
    telemetry = request.telemetry
    
    # 1. Anomaly Detection
    anom_req = AnomalyRequest(machine_id=machine_id, telemetry=telemetry)
    anomaly_res = detect_anomalies(anom_req)
    
    # 2. Root Cause Analysis
    rca_req = RCARequest(machine_id=machine_id, telemetry=telemetry, anomaly=anomaly_res)
    rca_res = analyze_root_cause(rca_req)
    
    # 3. Impact Prediction
    impact_req = ImpactRequest(machine_id=machine_id, telemetry=telemetry, anomaly=anomaly_res, rca=rca_res)
    impact_res = predict_impact(impact_req)
    
    # 4. What-if Recovery Simulation (Evaluate all 4 standard actions)
    actions = [
        RecoveryAction(action_id="STOP_MAINTAIN", name="Stop & Maintain", description="Halt production for immediate maintenance."),
        RecoveryAction(action_id="DERATE_SPEED", name="Derate Speed", description="Reduce machine speed to lower stress."),
        RecoveryAction(action_id="REROUTE_WORKLOAD", name="Reroute Workload", description="Shift load to parallel line."),
        RecoveryAction(action_id="CONTINUE_UNCHECKED", name="Continue Unchecked", description="Take no action.")
    ]
    
    simulations = []
    for action in actions:
        rec_req = RecoverySimulationRequest(
            machine_id=machine_id,
            telemetry=telemetry,
            anomaly=anomaly_res,
            rca=rca_res,
            impact=impact_res,
            action=action
        )
        sim_res = simulate_recovery(rec_req)
        simulations.append(sim_res)
        
    # 5. Decision Engine
    from .models import DecisionRequest
    dec_req = DecisionRequest(
        machine_id=machine_id,
        telemetry=telemetry,
        anomaly=anomaly_res,
        rca=rca_res,
        impact=impact_res,
        recovery_options=simulations
    )
    decision_res = make_decision(dec_req)
    
    # Combine results
    return PipelineResult(
        machine_id=machine_id,
        anomaly=anomaly_res,
        rca=rca_res,
        impact=impact_res,
        recovery_simulations=simulations,
        decision=decision_res
    )
