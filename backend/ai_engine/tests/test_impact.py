import pytest
import sys
import os
import numpy as np
from datetime import datetime

# Ensure backend can be imported
BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from ai_engine.models import ImpactRequest, AnomalyRequest, RCARequest
from ai_engine.anomaly import detect_anomalies
from ai_engine.rca import analyze_root_cause
from ai_engine.impact import predict_impact
from src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    NORMAL_02_HIGH_DEMAND_STABLE,
    NORMAL_03_MINOR_VARIATION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def get_impact_request(scenario, severity=0.0, seed=42, machine_id="M03", remove_tput=False, remove_all=False):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, 12, 0, 0)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity, start_time=start)
    
    t_dict = t.model_dump()
    if remove_tput:
        t_dict.pop("throughput", None)
    if remove_all:
        t_dict = {"state": "HEALTHY"}
        
    anom_req = AnomalyRequest(machine_id="M03", telemetry=t_dict)
    anom_res = detect_anomalies(anom_req)
    
    rca_req = RCARequest(machine_id="M03", telemetry=t_dict, anomaly=anom_res, maintenance_history=[])
    rca_res = analyze_root_cause(rca_req)
    
    req = ImpactRequest(
        machine_id=machine_id, # Can override machine_id here for baseline tests
        telemetry=t_dict,
        anomaly=anom_res,
        rca=rca_res
    )
    return req

# A. Healthy complete telemetry
def test_healthy_machine():
    req = get_impact_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    res = predict_impact(req)
    
    assert res.impact.production.loss_rate < 0.1
    assert res.impact.downtime.risk_score < 0.2
    assert res.confidence >= 0.8
    assert res.impact.downtime.observed_minutes == 0

# B. Cooling degradation
def test_cooling_degradation():
    req = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = predict_impact(req)
    
    assert res.impact.production.loss_rate > 0.1
    assert res.impact.downtime.risk_score > 0.5
    assert "temperature" in str(res.evidence).lower() or "throughput" in str(res.evidence).lower()

# C. Bearing degradation
def test_bearing_degradation():
    req = get_impact_request(DISRUPTION_02_BEARING_DEGRADATION, severity=1.0)
    res = predict_impact(req)
    
    assert res.impact.downtime.risk_score > 0.6
    assert res.impact.production.loss_rate > 0.1

# D. Throughput degradation
def test_throughput_degradation():
    req = get_impact_request(DISRUPTION_03_THROUGHPUT_DEGRADATION, severity=1.0)
    res = predict_impact(req)
    
    assert res.impact.production.loss_rate > 0.4
    assert res.impact.downtime.observed_minutes == 0 

# E. Missing throughput
def test_missing_throughput():
    req = get_impact_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0, remove_tput=True)
    res = predict_impact(req)
    
    assert res.impact.production.current_throughput is None
    assert res.impact.production.loss_rate is None
    assert res.impact.production.estimated_loss_per_hour is None
    assert res.impact.orders.affected_orders is None
    assert "Throughput telemetry is missing" in str(res.assumptions)
    assert res.confidence < 1.0

# F. Missing required telemetry
def test_missing_required_telemetry():
    req = get_impact_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0, remove_all=True)
    res = predict_impact(req)
    
    assert res.impact.production.current_throughput is None
    assert res.impact.production.loss_rate is None
    assert res.confidence < 1.0

# G. Missing baseline
def test_missing_weak_baseline():
    req = get_impact_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0, machine_id="UNKNOWN_M")
    res = predict_impact(req)
    
    assert res.confidence < 1.0
    assert "Machine configuration not found" in res.assumptions[0]

# H. Weak RCA confidence
def test_weak_rca_confidence():
    req = get_impact_request(NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    # mock a high anomaly but weak RCA
    req.anomaly.is_anomaly = True
    req.anomaly.anomaly_score = 0.9
    req.rca.probable_cause.confidence = 0.2
    
    res = predict_impact(req)
    # Confidence penalty (-0.15) applied because RCA < 0.5
    assert res.confidence < 1.0

# I. Strong evidence
def test_strong_evidence():
    req = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    # Force extreme temp deviation to trigger the boost
    req.telemetry["temperature"] = 100.0
    res = predict_impact(req)
    
    # Check that confidence gets a boost for specific severe evidence aligning with impact
    # In cooling, RCA confidence is not 1.0, so this ensures it doesn't just copy RCA
    assert res.confidence > req.rca.probable_cause.confidence

# J. Projected downtime unavailable without supporting duration evidence
# K. No arbitrary 120-minute calculation
def test_no_arbitrary_projection():
    req = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = predict_impact(req)
    
    assert res.impact.downtime.projected_minutes is None
    assert "Projected downtime unavailable" in str(res.assumptions)

# L. Deterministic repeatability
def test_deterministic_repeatability():
    req1 = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.8, seed=10)
    res1 = predict_impact(req1)
    
    req2 = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.8, seed=10)
    res2 = predict_impact(req2)
    
    assert res1.model_dump() == res2.model_dump()

# M. Financial impact remains null
# N. No fabricated numerical values
def test_no_fabricated_financial_impact():
    req = get_impact_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    res = predict_impact(req)
    
    assert res.impact.financial.estimated_loss is None
    assert res.impact.financial.currency is None
