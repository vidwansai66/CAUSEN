import pytest
import sys
import os
import numpy as np
from datetime import datetime

# Ensure backend can be imported
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# Ensure simulation can be imported
SIM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "simulation"))
if SIM_PATH not in sys.path:
    sys.path.insert(0, SIM_PATH)

from ai_engine.models import AnomalyRequest
from ai_engine.anomaly import detect_anomalies
from src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    NORMAL_02_HIGH_DEMAND_STABLE,
    NORMAL_03_MINOR_VARIATION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def get_telemetry(scenario, severity=0.0, seed=42):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, 12, 0, 0)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity, start_time=start)
    return AnomalyRequest(machine_id="M03", telemetry=t.model_dump())

def test_normal_stable():
    req = get_telemetry(NORMAL_01_STABLE_PRODUCTION)
    res = detect_anomalies(req)
    assert not res.is_anomaly
    assert res.anomaly_score < 0.25
    assert res.severity == "NORMAL"

def test_normal_high_demand():
    req = get_telemetry(NORMAL_02_HIGH_DEMAND_STABLE)
    res = detect_anomalies(req)
    # High demand should not falsely trigger an anomaly
    assert not res.is_anomaly
    assert res.anomaly_score < 0.25

def test_normal_minor_variation():
    req = get_telemetry(NORMAL_03_MINOR_VARIATION)
    res = detect_anomalies(req)
    # Should still be within tolerances
    assert not res.is_anomaly

def test_cooling_anomaly():
    req = get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = detect_anomalies(req)
    assert res.is_anomaly
    
    # Temperature should be the major contributor
    temp_sig = next((s for s in res.signals if s.name == "temperature"), None)
    assert temp_sig is not None
    assert temp_sig.direction == "HIGH"
    assert temp_sig.contribution > 0.5
    
    # Verify temperature is one of the highest contributors
    sorted_sigs = sorted(res.signals, key=lambda x: x.contribution, reverse=True)
    assert sorted_sigs[0].name == "temperature" or sorted_sigs[1].name == "temperature"

def test_bearing_anomaly():
    req = get_telemetry(DISRUPTION_02_BEARING_DEGRADATION, severity=1.0)
    res = detect_anomalies(req)
    assert res.is_anomaly
    
    vib_sig = next((s for s in res.signals if s.name == "vibration"), None)
    assert vib_sig is not None
    assert vib_sig.direction == "HIGH"
    assert vib_sig.contribution > 0.5

    sorted_sigs = sorted(res.signals, key=lambda x: x.contribution, reverse=True)
    assert sorted_sigs[0].name == "vibration"

def test_throughput_anomaly():
    req = get_telemetry(DISRUPTION_03_THROUGHPUT_DEGRADATION, severity=1.0)
    res = detect_anomalies(req)
    assert res.is_anomaly
    
    tput_sig = next((s for s in res.signals if s.name == "throughput"), None)
    assert tput_sig is not None
    assert tput_sig.direction == "LOW"
    assert tput_sig.contribution > 0.5

def test_anomaly_score_range():
    req = get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = detect_anomalies(req)
    assert 0.0 <= res.anomaly_score <= 1.0
    
    for sig in res.signals:
        assert 0.0 <= sig.contribution <= 1.0

def test_severity_progression():
    res_0 = detect_anomalies(get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.0))
    res_25 = detect_anomalies(get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.25))
    res_50 = detect_anomalies(get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.50))
    res_75 = detect_anomalies(get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.75))
    res_100 = detect_anomalies(get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0))
    
    assert res_0.anomaly_score <= res_25.anomaly_score
    assert res_25.anomaly_score <= res_50.anomaly_score
    assert res_50.anomaly_score <= res_75.anomaly_score
    assert res_75.anomaly_score <= res_100.anomaly_score
    
    assert res_0.severity == "NORMAL"
    assert res_100.severity in ["HIGH", "CRITICAL"]

def test_signal_evidence():
    req = get_telemetry(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.8)
    res = detect_anomalies(req)
    # Check that it identifies the correct signal formats
    temp_sig = next((s for s in res.signals if s.name == "temperature"), None)
    assert temp_sig is not None
    assert temp_sig.direction == "HIGH"
    assert "baseline" in temp_sig.model_dump()
    assert "current" in temp_sig.model_dump()
    assert "deviation_percent" in temp_sig.model_dump()
    assert "contribution" in temp_sig.model_dump()
    assert temp_sig.contribution > 0.0
    
def test_severity_boundaries():
    from ai_engine.anomaly import map_severity
    assert map_severity(0.0) == "NORMAL"
    assert map_severity(0.24) == "NORMAL"
    assert map_severity(0.25) == "LOW"
    assert map_severity(0.49) == "LOW"
    assert map_severity(0.50) == "MEDIUM"
    assert map_severity(0.74) == "MEDIUM"
    assert map_severity(0.75) == "HIGH"
    assert map_severity(0.89) == "HIGH"
    assert map_severity(0.90) == "CRITICAL"
    assert map_severity(1.00) == "CRITICAL"

def test_deterministic_result():
    req1 = get_telemetry(DISRUPTION_02_BEARING_DEGRADATION, severity=0.6, seed=123)
    res1 = detect_anomalies(req1)
    
    req2 = get_telemetry(DISRUPTION_02_BEARING_DEGRADATION, severity=0.6, seed=123)
    res2 = detect_anomalies(req2)
    
    assert res1.model_dump() == res2.model_dump()
