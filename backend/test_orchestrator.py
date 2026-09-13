import pytest
from ai_engine.orchestrator import run_ai_pipeline
from ai_engine.models import PipelineRequest
from simulation.src.scenario_engine import generate_telemetry, DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, DISRUPTION_02_BEARING_DEGRADATION, DISRUPTION_03_THROUGHPUT_DEGRADATION
import numpy as np

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_pipeline_normal(rng):
    t = generate_telemetry("M03", 10, rng)
    req = PipelineRequest(machine_id="M03", telemetry=t.model_dump())
    res = run_ai_pipeline(req)
    
    assert res.anomaly.is_anomaly is False
    assert res.decision.decision.recommended_action == "NO_ACTION"

def test_pipeline_cooling_disruption(rng):
    t = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    req = PipelineRequest(machine_id="M03", telemetry=t.model_dump())
    res = run_ai_pipeline(req)
    
    assert res.anomaly.is_anomaly is True
    assert "Cooling" in res.rca.probable_cause.name or "Temperature" in res.rca.probable_cause.name
    
    # Check decision
    assert res.decision.decision.recommended_action == "STOP_MAINTAIN"
    
def test_pipeline_bearing_disruption(rng):
    t = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_02_BEARING_DEGRADATION, severity=1.0)
    req = PipelineRequest(machine_id="M03", telemetry=t.model_dump())
    res = run_ai_pipeline(req)
    
    assert res.anomaly.is_anomaly is True
    assert res.decision.decision.recommended_action == "STOP_MAINTAIN"

def test_pipeline_throughput_disruption(rng):
    t = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_03_THROUGHPUT_DEGRADATION, severity=1.0)
    req = PipelineRequest(machine_id="M03", telemetry=t.model_dump())
    res = run_ai_pipeline(req)
    
    assert res.anomaly.is_anomaly is True
    assert res.decision.decision.recommended_action == "STOP_MAINTAIN"

def test_no_side_effects(rng):
    t = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    req = PipelineRequest(machine_id="M03", telemetry=t.model_dump())
    res1 = run_ai_pipeline(req)
    res2 = run_ai_pipeline(req)
    
    # Must be perfectly deterministic
    assert res1.model_dump() == res2.model_dump()
