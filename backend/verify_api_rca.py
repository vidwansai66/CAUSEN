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

def test_rca_scenario(name, scenario, severity):
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
        
    result = response_rca.json()
    print(f"--- {name.upper()} ---")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    print("Testing RCA API...")
    res_normal = test_rca_scenario("Healthy", NORMAL_01_STABLE_PRODUCTION, 0.0)
    assert res_normal["probable_cause"]["name"] == "Normal Operation"
    
    res_cooling = test_rca_scenario("Cooling Anomaly", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    assert res_cooling["probable_cause"]["name"] == "Cooling System Degradation"
    
    res_bearing = test_rca_scenario("Bearing Anomaly", DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    assert res_bearing["probable_cause"]["name"] == "Bearing / Mechanical Degradation"
    
    res_throughput = test_rca_scenario("Throughput Anomaly", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
    assert res_throughput["probable_cause"]["name"] == "Throughput / Production Degradation"
    
    print("All RCA API tests passed!")
