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
    assert anomaly_response.status_code == 200
    anomaly_result = anomaly_response.json()
    
    # 2. RCA
    rca_response = requests.post(RCA_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "maintenance_history": []
    })
    assert rca_response.status_code == 200
    rca_result = rca_response.json()
    
    # 3. Impact
    impact_response = requests.post(IMPACT_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "rca": rca_result
    })
    assert impact_response.status_code == 200
    impact_result = impact_response.json()
    
    # 4. Recovery
    # Check side effect safety by saving a deepcopy
    original_t_dict = copy.deepcopy(t_dict)
    
    recovery_response = requests.post(RECOVERY_URL, json={
        "machine_id": "M03",
        "telemetry": t_dict,
        "anomaly": anomaly_result,
        "rca": rca_result,
        "impact": impact_result,
        "action": {
            "action_id": action_id,
            "name": "Test Action",
            "description": "Triggered via API test"
        }
    })
    if recovery_response.status_code != 200:
        print("Error Response:", recovery_response.text)
    assert recovery_response.status_code == 200
    recovery_result = recovery_response.json()
    
    # Safety assertion
    assert original_t_dict == t_dict
    
    print(f"\n--- {title.upper()} ---")
    print(f"Action: {action_id}")
    print(f"Before Anomaly Score: {recovery_result['before']['anomaly_score']}")
    print(f"After Anomaly Score:  {recovery_result['after']['anomaly_score']}")
    print(f"Before Downtime Risk: {recovery_result['before']['downtime_risk']}")
    print(f"After Downtime Risk:  {recovery_result['after']['downtime_risk']}")
    print(f"Effectiveness:        {recovery_result['recovery_effectiveness']}")
    print(f"Explanation:          {recovery_result['explanation']}")
    
    return recovery_result

if __name__ == "__main__":
    print("Testing Recovery API...")
    
    test_recovery_scenario("Cooling Disruption -> Stop/Maintain", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "STOP_MAINTAIN")
    test_recovery_scenario("Bearing Disruption -> Derate Speed", DISRUPTION_02_BEARING_DEGRADATION, 1.0, "DERATE_SPEED")
    test_recovery_scenario("Throughput Disruption -> Reroute Workload", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0, "REROUTE_WORKLOAD")
    test_recovery_scenario("Invalid Action", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0, "INVALID_ACTION")
    
    print("\nAll Recovery API tests completed successfully!")
