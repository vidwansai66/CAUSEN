import pytest
import sys
import os
import numpy as np
from datetime import datetime

# Ensure backend can be imported
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from ai_engine.models import RCARequest, AnomalyRequest
from ai_engine.anomaly import detect_anomalies
from ai_engine.rca import analyze_root_cause
from src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def get_rca_request(scenario, severity=0.0, seed=42, maintenance=None):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, 12, 0, 0)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity, start_time=start)
    
    anom_req = AnomalyRequest(machine_id="M03", telemetry=t.model_dump())
    anom_res = detect_anomalies(anom_req)
    
    return RCARequest(
        machine_id="M03",
        telemetry=t.model_dump(),
        anomaly=anom_res,
        maintenance_history=maintenance
    )

def test_cooling_degradation_cause():
    req = get_rca_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = analyze_root_cause(req)
    
    assert res.probable_cause.name == "Cooling System Degradation"
    assert res.probable_cause.confidence > 0.5

def test_bearing_degradation_cause():
    req = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=1.0)
    res = analyze_root_cause(req)
    
    assert res.probable_cause.name == "Bearing / Mechanical Degradation"
    assert res.probable_cause.confidence > 0.5

def test_throughput_degradation_cause():
    req = get_rca_request(DISRUPTION_03_THROUGHPUT_DEGRADATION, severity=1.0)
    res = analyze_root_cause(req)
    
    assert res.probable_cause.name == "Throughput / Production Degradation"
    assert res.probable_cause.confidence > 0.5

def test_normal_healthy_telemetry():
    req = get_rca_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    res = analyze_root_cause(req)
    
    assert res.probable_cause.name == "Normal Operation"
    assert res.probable_cause.confidence == 1.0

def test_ambiguous_abnormal_telemetry():
    # Provide a case where it's anomalous but neither cooling, bearing, nor throughput matches perfectly.
    # We can fake the anomaly object to represent something unknown.
    req = get_rca_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    req.anomaly.is_anomaly = True
    req.anomaly.anomaly_score = 0.8
    req.anomaly.severity = "HIGH"
    # Signals list is empty in healthy case, so RCA won't find any specific matches.
    
    res = analyze_root_cause(req)
    assert res.probable_cause.name == "Unknown / Insufficient Evidence"
    assert res.probable_cause.confidence < 0.5

def test_confidence_bounds():
    req = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=1.0, maintenance=[{"notes": "Bearing overdue"}])
    res = analyze_root_cause(req)
    assert 0.0 <= res.probable_cause.confidence <= 1.0

def test_evidence_from_actual_telemetry():
    req = get_rca_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = analyze_root_cause(req)
    
    ev_signals = [e.signal for e in res.evidence]
    assert "temperature" in ev_signals
    assert "throughput" in ev_signals or "cycle_time" in ev_signals

def test_deterministic_rca():
    req1 = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=0.7, seed=123)
    res1 = analyze_root_cause(req1)
    
    req2 = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=0.7, seed=123)
    res2 = analyze_root_cause(req2)
    
    assert res1.model_dump() == res2.model_dump()

def test_maintenance_history_boost():
    req_no_hist = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=0.5)
    res_no_hist = analyze_root_cause(req_no_hist)
    
    req_with_hist = get_rca_request(DISRUPTION_02_BEARING_DEGRADATION, severity=0.5, maintenance=[{"record": "bearing replacement"}])
    res_with_hist = analyze_root_cause(req_with_hist)
    
    assert res_with_hist.probable_cause.confidence > res_no_hist.probable_cause.confidence
    # Ensure it doesn't override contradictory telemetry by testing a cooling failure with bearing history
    req_contradictory = get_rca_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0, maintenance=[{"record": "bearing"}])
    res_contra = analyze_root_cause(req_contradictory)
    
    # Cooling should still win over bearing because the actual telemetry screams cooling
    assert res_contra.probable_cause.name == "Cooling System Degradation"

def test_competing_synthetic_causes():
    # Create a synthetic anomaly request where temp is HIGH, vib is HIGH, throughput is LOW.
    # This should evaluate competing causes and pick the strongest.
    req = get_rca_request(NORMAL_01_STABLE_PRODUCTION)
    # Mock the anomaly
    req.anomaly.anomaly_score = 1.0
    req.anomaly.signals = []
    
    from ai_engine.models import SignalEvidence
    req.anomaly.signals.append(SignalEvidence(
        name="temperature", baseline=42.0, current=70.0, deviation_percent=66.0, direction="HIGH", contribution=1.0
    ))
    req.anomaly.signals.append(SignalEvidence(
        name="vibration", baseline=1.2, current=5.5, deviation_percent=350.0, direction="HIGH", contribution=1.0
    ))
    req.anomaly.signals.append(SignalEvidence(
        name="throughput", baseline=1400.0, current=800.0, deviation_percent=-42.0, direction="LOW", contribution=0.7
    ))
    
    res = analyze_root_cause(req)
    
    # Since both cooling and bearing get high scores, we should see alternatives
    assert res.probable_cause.name in ["Cooling System Degradation", "Bearing / Mechanical Degradation"]
    assert len(res.alternatives) > 0
    alt_names = [a.name for a in res.alternatives]
    if res.probable_cause.name == "Cooling System Degradation":
        assert "Bearing / Mechanical Degradation" in alt_names
    else:
        assert "Cooling System Degradation" in alt_names
