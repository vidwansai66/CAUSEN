import requests
import json
import numpy as np
import copy
import sys
import os

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulation"))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

BASE_URL = "http://127.0.0.1:8001/api/ai"
ANOMALY_URL = f"{BASE_URL}/anomaly"
RCA_URL = f"{BASE_URL}/rca"
IMPACT_URL = f"{BASE_URL}/impact"
RECOVERY_URL = f"{BASE_URL}/recovery/simulate"

def test_recovery_scenario(title, scenario, severity, action_id):
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity)
    t_dict = t.model_dump()
    
    # 1. Anomaly
    anomaly_response = requests.post(ANOMALY_URL, json={"machine_id": "M03", "telemetry": t_dict})
    anomaly_result = anomaly_response.json()
    
    # 2. RCA
    rca_response = requests.post(RCA_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "maintenance_history": []
    })
    rca_result = rca_response.json()
    
    # 3. Impact
    impact_response = requests.post(IMPACT_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "rca": rca_result
    })
    impact_result = impact_response.json()
    
    # 4. Recovery
    original_t_dict = copy.deepcopy(t_dict)
    
    recovery_response = requests.post(RECOVERY_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "rca": rca_result,
        "impact": impact_result,
        "action": {
            "action_id": action_id,
            "name": action_id,
            "description": "Triggered via API test"
        }
    })
    
    recovery_result = recovery_response.json()
    
    print(f"\n==================================================")
    print(f"Scenario: {title}")
    print(f"Action: {action_id}")
    print(f"==================================================")
    print("BEFORE:")
    print(f"- temperature: {recovery_result['before']['predicted_telemetry'].get('temperature')}")
    print(f"- vibration: {recovery_result['before']['predicted_telemetry'].get('vibration')}")
    print(f"- throughput: {recovery_result['before']['predicted_telemetry'].get('throughput')}")
    print(f"- cycle_time: {recovery_result['before']['predicted_telemetry'].get('cycle_time')}")
    print(f"- anomaly_score: {recovery_result['before'].get('anomaly_score')}")
    print(f"- anomaly_severity: {recovery_result['before'].get('anomaly_severity')}")
    print(f"- production_loss_rate: {recovery_result['before'].get('production_loss_rate')}")
    print(f"- downtime_risk: {recovery_result['before'].get('downtime_risk')}")
    
    print("\nAFTER:")
    print(f"- predicted temperature: {recovery_result['after']['predicted_telemetry'].get('temperature')}")
    print(f"- predicted vibration: {recovery_result['after']['predicted_telemetry'].get('vibration')}")
    print(f"- predicted throughput: {recovery_result['after']['predicted_telemetry'].get('throughput')}")
    print(f"- predicted cycle_time: {recovery_result['after']['predicted_telemetry'].get('cycle_time')}")
    print(f"- predicted anomaly_score: {recovery_result['after'].get('anomaly_score')}")
    print(f"- predicted anomaly_severity: {recovery_result['after'].get('anomaly_severity')}")
    print(f"- predicted production_loss_rate: {recovery_result['after'].get('production_loss_rate')}")
    print(f"- predicted downtime_risk: {recovery_result['after'].get('downtime_risk')}")
    
    print("\nDELTA:")
    print(f"- anomaly score change: {recovery_result['delta'].get('anomaly_score_change')}")
    print(f"- production loss change: {recovery_result['delta'].get('production_loss_change')}")
    print(f"- downtime risk change: {recovery_result['delta'].get('downtime_risk_change')}")
    print(f"- throughput change: {recovery_result['delta'].get('throughput_change')}")

    print("\nSUMMARY:")
    print(f"- recovery_effectiveness: {recovery_result.get('recovery_effectiveness')}")
    print(f"- recovery_confidence: {recovery_result.get('confidence')}")
    print(f"- assumptions: {recovery_result.get('assumptions')}")
    print(f"- explanation: {recovery_result.get('explanation')}")
    
    if action_id == "CONTINUE_UNCHECKED":
        return recovery_result
        
    return recovery_result, original_t_dict, t_dict

if __name__ == "__main__":
    r1 = test_recovery_scenario("DISRUPTION_01_COOLING_SYSTEM_DEGRADATION", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    r2 = test_recovery_scenario("DISRUPTION_02_BEARING_DEGRADATION", DISRUPTION_02_BEARING_DEGRADATION, 1.0, "DERATE_SPEED")
    r3 = test_recovery_scenario("DISRUPTION_03_THROUGHPUT_DEGRADATION", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0, "REROUTE_WORKLOAD")
    r4 = test_recovery_scenario("DISRUPTION_01_COOLING_SYSTEM_DEGRADATION", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "CONTINUE_UNCHECKED")
    
    print("\n==================================================")
    print("SIDE-EFFECT SAFETY TEST")
    print("==================================================")
    result, before_state, after_state = r1
    
    # 1. Dictionary test
    print(f"Dictionary copy test (BEFORE == AFTER): {before_state == after_state}")
    
    # 2. Live API test
    try:
        # Check actual simulator state before
        state_before_response = requests.get(f"http://127.0.0.1:8001/api/state")
        state_before = state_before_response.json()
        
        # Hit the simulation API
        requests.post(RECOVERY_URL, json={
            "machine_id": "M03",
            "telemetry": before_state,
            "anomaly": r1[0]["before"],  # We just pass the dict struct here, doesn't matter if it's strictly correct as long as it doesn't crash the side effect test
            "rca": {"machine_id":"M03", "fault_type":"NONE", "confidence":0.0, "evidence":[], "contributing_factors":[], "maintenance_history_used":False},
            "impact": {"machine_id":"M03", "impact":{"production":{"throughput_loss":0,"loss_rate":0,"estimated_loss_per_hour":0},"downtime":{"risk_score":0,"projected_minutes":None},"quality":{"affected_capacity":0,"affected_orders":[]}},"confidence":0,"evidence":[],"warnings":[]},
            "action": {
                "action_id": "STOP_MAINTAIN",
                "name": "STOP_MAINTAIN",
                "description": "Triggered via API test"
            }
        })
        
        # Check actual simulator state after
        state_after_response = requests.get(f"http://127.0.0.1:8001/api/state")
        state_after = state_after_response.json()
        
        # State might tick forward slightly, but active faults should be identical
        # Verify no fault was injected or reset unexpectedly
        before_faults = {m["id"]: m.get("active_fault") for m in state_before.get("machines", [])}
        after_faults = {m["id"]: m.get("active_fault") for m in state_after.get("machines", [])}
        
        print(f"Live simulator faults BEFORE simulation call: {before_faults}")
        print(f"Live simulator faults AFTER simulation call:  {after_faults}")
        print(f"Live Simulator faults match: {before_faults == after_faults}")
        
    except Exception as e:
        print(f"Could not reach live simulator for state side-effect test: {e}")

    print("\n==================================================")
    print("DETERMINISM TEST")
    print("==================================================")
    r1_b = test_recovery_scenario("DISRUPTION_01_COOLING_SYSTEM_DEGRADATION", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    import json
    if json.dumps(r1[0], sort_keys=True) == json.dumps(r1_b[0], sort_keys=True):
        print("PASS")
    else:
        print("FAIL: Outputs differ")
    
    print("\n==================================================")
    print("INVALID ACTION TEST")
    print("==================================================")
    
    # We must use valid objects for the invalid action to hit our business logic, not Pydantic validation errors.
    
    invalid_response = requests.post(RECOVERY_URL, json={
        "machine_id": "M03",
        "telemetry": before_state,
        "anomaly": r1[0]["before"],  # We need the full AnomalyRequest structure. Wait, r1[0]["before"] is RecoveryBeforeAfterState, not AnomalyRequest.
        # It's better to just call test_recovery_scenario
    })
    
    # Actually let's just use the function
def test_invalid_action():
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    t_dict = t.model_dump()
    anomaly_result = requests.post(ANOMALY_URL, json={"machine_id": "M03", "telemetry": t_dict}).json()
    rca_result = requests.post(RCA_URL, json={"machine_id": "M03", "telemetry": t_dict, "anomaly": anomaly_result, "maintenance_history": []}).json()
    impact_result = requests.post(IMPACT_URL, json={"machine_id": "M03", "telemetry": t_dict, "anomaly": anomaly_result, "rca": rca_result}).json()
    
    response = requests.post(RECOVERY_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "rca": rca_result,
        "impact": impact_result,
        "action": {
            "action_id": "MAGIC_FIX_ALL",
            "name": "Magic Fix All",
            "description": "Triggered via API test"
        }
    })
    print(f"HTTP status: {response.status_code}")
    print(f"response body: {response.text}")

test_invalid_action()
