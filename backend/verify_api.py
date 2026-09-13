import requests
import json
import sys
import os

# Add simulation to path to generate test telemetry
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulation")))
from src.scenario_engine import generate_telemetry
from src.scenario_engine import NORMAL_01_STABLE_PRODUCTION, DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, DISRUPTION_02_BEARING_DEGRADATION, DISRUPTION_03_THROUGHPUT_DEGRADATION
import numpy as np

API_URL = "http://localhost:8001/api/ai/anomaly"

def test_scenario(name, scenario, severity):
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity)
    payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump()
    }
    
    response = requests.post(API_URL, json=payload)
    if response.status_code != 200:
        print(f"Error testing {name}: {response.text}")
        return None
        
    result = response.json()
    print(f"--- {name.upper()} ---")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    print("Testing API...")
    res_normal = test_scenario("Healthy", NORMAL_01_STABLE_PRODUCTION, 0.0)
    assert res_normal["is_anomaly"] == False
    assert res_normal["severity"] == "NORMAL"
    
    res_cooling = test_scenario("Cooling Anomaly", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    assert res_cooling["is_anomaly"] == True
    
    res_bearing = test_scenario("Bearing Anomaly", DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    assert res_bearing["is_anomaly"] == True
    
    res_throughput = test_scenario("Throughput Anomaly", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
    assert res_throughput["is_anomaly"] == True
    print("All API tests passed!")
