import pytest
import sys
import os
import numpy as np
from datetime import datetime

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from ai_engine.models import (
    RecoverySimulationRequest,
    RecoveryAction,
    AnomalyRequest,
    RCARequest,
    ImpactRequest
)
from ai_engine.anomaly import detect_anomalies
from ai_engine.rca import analyze_root_cause
from ai_engine.impact import predict_impact
from ai_engine.recovery import simulate_recovery

from src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def get_base_request(scenario, severity, action_id, seed=42, remove_tput=False):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, 12, 0, 0)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity, start_time=start)
    
    t_dict = t.model_dump()
    if remove_tput:
        t_dict.pop("throughput", None)
        
    anom_req = AnomalyRequest(machine_id="M03", telemetry=t_dict)
    anom_res = detect_anomalies(anom_req)
    
    rca_req = RCARequest(machine_id="M03", telemetry=t_dict, anomaly=anom_res, maintenance_history=[])
    rca_res = analyze_root_cause(rca_req)
    
    imp_req = ImpactRequest(machine_id="M03", telemetry=t_dict, anomaly=anom_res, rca=rca_res)
    imp_res = predict_impact(imp_req)
    
    action = RecoveryAction(action_id=action_id, name="Test Action", description="Description")
    
    return RecoverySimulationRequest(
        machine_id="M03",
        telemetry=t_dict,
        anomaly=anom_res,
        rca=rca_res,
        impact=imp_res,
        action=action
    )

def test_healthy_machine_valid_action():
    req = get_base_request(NORMAL_01_STABLE_PRODUCTION, 0.0, "CONTINUE_UNCHECKED")
    res = simulate_recovery(req)
    
    assert res.before.anomaly_score == 0
    assert res.recovery_effectiveness == 1.0 # Already healthy

def test_cooling_degradation_recovery():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    res = simulate_recovery(req)
    
    assert res.before.anomaly_score > 0.8
    # Anomaly score might spike because throughput goes to 0, but risk drops
    assert res.delta.downtime_risk_change < 0
    assert 0.0 <= res.recovery_effectiveness <= 1.0

def test_bearing_degradation_recovery():
    req = get_base_request(DISRUPTION_02_BEARING_DEGRADATION, 1.0, "DERATE_SPEED")
    res = simulate_recovery(req)
    
    assert res.before.anomaly_score > 0.8
    assert res.after.anomaly_score < 0.8
    assert res.delta.anomaly_score_change < 0

def test_throughput_degradation_recovery():
    req = get_base_request(DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0, "REROUTE_WORKLOAD")
    res = simulate_recovery(req)
    
    assert res.after.predicted_telemetry["throughput"] == 1400.0 * 0.20

def test_partial_recovery():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "DERATE_SPEED")
    res = simulate_recovery(req)
    
    assert res.recovery_effectiveness > 0
    assert res.recovery_effectiveness < 1.0 # Should not be perfect

def test_ineffective_recovery():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "CONTINUE_UNCHECKED")
    res = simulate_recovery(req)
    
    assert res.recovery_effectiveness < 0.1
    assert "ineffective" in res.explanation.lower()

def test_invalid_action():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "MAGIC_FIX_ALL")
    res = simulate_recovery(req)
    
    assert res.recovery_effectiveness == 0.0
    assert "Unsupported action" in str(res.assumptions)
    assert res.delta.anomaly_score_change == 0

def test_missing_telemetry():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN", remove_tput=True)
    res = simulate_recovery(req)
    
    assert res.confidence < 1.0
    assert "Missing throughput telemetry" in str(res.assumptions)

def test_side_effect_safety():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    
    original_tput = req.telemetry["throughput"]
    simulate_recovery(req)
    
    assert req.telemetry["throughput"] == original_tput # Ensure dict was NOT mutated

def test_deterministic_repeatability():
    req1 = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 0.8, "STOP_MAINTAIN", seed=10)
    res1 = simulate_recovery(req1)
    
    req2 = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 0.8, "STOP_MAINTAIN", seed=10)
    res2 = simulate_recovery(req2)
    
    assert res1.model_dump() == res2.model_dump()

def test_effectiveness_confidence_bounds():
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    res = simulate_recovery(req)
    
    assert 0.0 <= res.recovery_effectiveness <= 1.0
    assert 0.0 <= res.confidence <= 1.0

def test_confidence_strong_evidence_relevant_action():
    # A. Complete telemetry + valid relevant action + strong evidence -> high confidence
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    res = simulate_recovery(req)
    assert res.confidence >= 0.8 # Based on formula (0.2 + 0.2 + 0.1 + 0.4 - 0.1)

def test_confidence_weak_relevance():
    # D. Weak/unsupported action relevance -> lower confidence
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "REROUTE_WORKLOAD") # Reroute is for throughput degradation
    res = simulate_recovery(req)
    assert res.confidence < 0.9 
    
def test_confidence_missing_baseline():
    # C. Missing machine baseline -> reduced confidence
    req = get_base_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    req.machine_id = "UNKNOWN_MACHINE" # No baseline for this
    res = simulate_recovery(req)
    assert res.confidence == 0.0
