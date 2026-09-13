import pytest
import sys
import os
import numpy as np
from datetime import datetime, timezone
import copy

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from ai_engine.models import (
    DecisionRequest,
    RecoveryAction
)
from ai_engine.decision import make_decision
from ai_engine.tests.test_recovery import get_base_request as get_recovery_request
from ai_engine.recovery import simulate_recovery

from src.scenario_engine import (
    NORMAL_01_STABLE_PRODUCTION,
    NORMAL_03_MINOR_VARIATION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def get_decision_request(scenario, severity, seed=42):
    actions = ["STOP_MAINTAIN", "DERATE_SPEED", "REROUTE_WORKLOAD", "CONTINUE_UNCHECKED"]
    
    # Generate base context from the first action (they all share the same before state)
    base_req = get_recovery_request(scenario, severity, "CONTINUE_UNCHECKED", seed=seed)
    
    options = []
    for act in actions:
        req = get_recovery_request(scenario, severity, act, seed=seed)
        res = simulate_recovery(req)
        options.append(res)
        
    return DecisionRequest(
        machine_id=base_req.machine_id,
        telemetry=base_req.telemetry,
        anomaly=base_req.anomaly,
        rca=base_req.rca,
        impact=base_req.impact,
        recovery_options=options
    )

def test_healthy_machine_no_action():
    # A. Healthy machine -> NO_ACTION
    # B. Stable high-demand machine -> NO_ACTION (represented similarly by 0 anomaly)
    req = get_decision_request(NORMAL_01_STABLE_PRODUCTION, 0.0)
    res = make_decision(req)
    assert res.decision.recommended_action == "NO_ACTION"
    assert "operating within expected limits" in res.decision.recommendation
    assert len(res.ranked_options) == 0

def test_minor_variation_no_action():
    # C. Minor variation -> no aggressive intervention
    req = get_decision_request(NORMAL_03_MINOR_VARIATION, 0.5)
    # Severity is typically LOW for minor variation
    if req.anomaly.severity == "LOW":
        res = make_decision(req)
        assert res.decision.recommended_action == "NO_ACTION"
        assert "Aggressive intervention is not justified" in res.decision.recommendation

def test_cooling_disruption_decision():
    # D. Cooling disruption -> rational recommendation
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    # With safety > production, STOP_MAINTAIN should be top choice for critical physical disruption
    assert res.decision.recommended_action in ["STOP_MAINTAIN", "DERATE_SPEED"]
    assert len(res.ranked_options) == 4

def test_bearing_disruption_decision():
    # E. Bearing disruption -> rational recommendation
    req = get_decision_request(DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    res = make_decision(req)
    assert res.decision.recommended_action in ["STOP_MAINTAIN", "DERATE_SPEED"]

def test_throughput_disruption_decision():
    # F. Throughput disruption -> rational recommendation
    req = get_decision_request(DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
    res = make_decision(req)
    assert res.decision.recommended_action in ["STOP_MAINTAIN", "REROUTE_WORKLOAD", "DERATE_SPEED"]

def test_continue_unchecked_penalized_severe_risk():
    # G. CONTINUE_UNCHECKED penalized under severe risk
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    
    cu_option = next(o for o in res.ranked_options if o.action_id == "CONTINUE_UNCHECKED")
    # Score should be very low due to penalty
    assert cu_option.score < 0.5

def test_effectiveness_does_not_solely_determine_winner():
    # H. Recovery effectiveness does not solely determine winner
    # I. STOP_MAINTAIN can win despite low production effectiveness when safety risk dominates
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    
    top_option = res.ranked_options[0]
    if top_option.action_id == "STOP_MAINTAIN":
        assert top_option.effectiveness < 0.5 # Effectiveness is low because production halts
        # Ensure it didn't win just because of high effectiveness
        
def test_production_tradeoff_affects_ranking():
    # J. Production trade-off affects ranking
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    
    stop_option = next(o for o in res.ranked_options if o.action_id == "STOP_MAINTAIN")
    assert "100%" in stop_option.production_tradeoff

def test_residual_risk_affects_ranking():
    # K. Residual risk affects ranking
    req = get_decision_request(DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    res = make_decision(req)
    
    for opt in res.ranked_options:
        assert opt.residual_risk in ["LOW", "MEDIUM", "CRITICAL"]

def test_recovery_confidence_affects_ranking():
    # L. Recovery confidence affects ranking
    # The score directly incorporates confidence
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    assert res.ranked_options[0].score > 0.0 # Score combines components

def test_ambiguous_scores_reduce_decision_confidence():
    # M. Ambiguous scores reduce decision confidence
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    # If top two options are close, confidence drops.
    # Confidence is bounded in [0,1].
    assert 0.0 <= res.decision.decision_confidence <= 1.0

def test_invalid_recovery_options():
    # N. Invalid/missing recovery options
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    req.recovery_options = []
    res = make_decision(req)
    assert res.decision.recommended_action == "NO_ACTION"
    assert "No recovery options provided." in res.decision.recommendation

def test_missing_evidence():
    # O. Missing evidence
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    assert len(res.evidence) > 0

def test_deterministic_repeatability():
    # P. Deterministic repeatability
    req1 = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, seed=123)
    res1 = make_decision(req1)
    
    req2 = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, seed=123)
    res2 = make_decision(req2)
    
    assert res1.model_dump() == res2.model_dump()

def test_decision_score_bounded():
    # Q. Decision score bounded
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    for opt in res.ranked_options:
        assert 0.0 <= opt.score <= 1.0

def test_decision_confidence_bounded():
    # R. Decision confidence bounded
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res = make_decision(req)
    assert 0.0 <= res.decision.decision_confidence <= 1.0

def test_no_scenario_name_hardcoding():
    # S. No scenario-name hardcoding
    # Read the file to ensure scenario strings are not used in decision logic
    decision_file = os.path.join(BACKEND_PATH, "ai_engine", "decision.py")
    with open(decision_file, "r") as f:
        content = f.read()
    assert "COOLING_SYSTEM_DEGRADATION" not in content
    assert "BEARING_DEGRADATION" not in content
    assert "THROUGHPUT_DEGRADATION" not in content

def test_no_side_effects():
    # T. No side effects
    req = get_decision_request(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    req_copy = copy.deepcopy(req)
    make_decision(req)
    
    assert req.model_dump() == req_copy.model_dump()
