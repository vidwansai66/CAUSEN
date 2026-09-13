import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulation")))
from src.scenario_engine import generate_telemetry
from src.scenario_engine import NORMAL_01_STABLE_PRODUCTION, DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, DISRUPTION_02_BEARING_DEGRADATION, DISRUPTION_03_THROUGHPUT_DEGRADATION
import numpy as np

ANOMALY_URL = "http://localhost:8001/api/ai/anomaly"
RCA_URL = "http://localhost:8001/api/ai/rca"
IMPACT_URL = "http://localhost:8001/api/ai/impact"

def test_impact_scenario(name, scenario, severity):
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity)
    
    # 1. Get Anomaly Result
    payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump()
    }
    
    response = requests.post(ANOMALY_URL, json=payload)
    if response.status_code != 200:
        print(f"Error testing Anomaly {name}: {response.text}")
        return None
    anomaly_result = response.json()
    
    # 2. Get RCA Result
    rca_payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump(),
        "anomaly": anomaly_result,
        "maintenance_history": [{"record": "bearing maintenance required"} if scenario == DISRUPTION_02_BEARING_DEGRADATION else {"record": "clean"}]
    }
    
    response_rca = requests.post(RCA_URL, json=rca_payload)
    if response_rca.status_code != 200:
        print(f"Error testing RCA {name}: {response_rca.text}")
        return None
    rca_result = response_rca.json()

    # 3. Get Impact Result
    impact_payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump(),
        "anomaly": anomaly_result,
        "rca": rca_result
    }

    response_impact = requests.post(IMPACT_URL, json=impact_payload)
    if response_impact.status_code != 200:
        print(f"Error testing Impact {name}: {response_impact.text}")
        return None
    impact_result = response_impact.json()

    print(f"--- {name.upper()} ---")
    print(json.dumps(impact_result, indent=2))
    
    # Cross-layer validation print
    print("\n[Cross-Layer Summary]")
    print(f"Machine: M03")
    print(f"Scenario: {scenario}")
    print(f"Anomaly Score: {anomaly_result['anomaly_score']}")
    print(f"Anomaly Severity: {anomaly_result['severity']}")
    print(f"Probable Cause: {rca_result['probable_cause']['name']}")
    print(f"RCA Confidence: {rca_result['probable_cause']['confidence']}")
    print(f"Production Impact (Loss Rate): {impact_result['impact']['production']['loss_rate']}")
    print(f"Downtime Risk: {impact_result['impact']['downtime']['risk_score']}")
    print(f"Impact Confidence: {impact_result['confidence']}\n")

    return impact_result

if __name__ == "__main__":
    print("Testing Impact API...")
    res_normal = test_impact_scenario("Healthy", NORMAL_01_STABLE_PRODUCTION, 0.0)
    res_cooling = test_impact_scenario("Cooling Anomaly", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    res_bearing = test_impact_scenario("Bearing Anomaly", DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    res_throughput = test_impact_scenario("Throughput Anomaly", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
    
    # Test missing throughput
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    t_dict = t.model_dump()
    t_dict.pop("throughput", None)
    
    anomaly_result = requests.post(ANOMALY_URL, json={"machine_id": "M03", "telemetry": t_dict}).json()
    rca_result = requests.post(RCA_URL, json={"machine_id": "M03", "telemetry": t_dict, "anomaly": anomaly_result, "maintenance_history": []}).json()
    impact_response = requests.post(IMPACT_URL, json={"machine_id": "M03", "telemetry": t_dict, "anomaly": anomaly_result, "rca": rca_result})
    assert impact_response.status_code == 200
    impact_result = impact_response.json()
    
    print("\n--- MISSING THROUGHPUT ---")
    print(f"Production Loss Rate: {impact_result['impact']['production']['loss_rate']}")
    print(f"Confidence: {impact_result['confidence']}")
    print(f"Assumptions: {impact_result['assumptions']}")
    
    print("All Impact API tests completed!")
