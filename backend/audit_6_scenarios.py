import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulation")))
from src.scenario_engine import generate_telemetry
from src.scenario_engine import (
    NORMAL_01_STABLE_PRODUCTION,
    NORMAL_02_HIGH_DEMAND_STABLE,
    NORMAL_03_MINOR_VARIATION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)
import numpy as np

ANOMALY_URL = "http://localhost:8001/api/ai/anomaly"
RCA_URL = "http://localhost:8001/api/ai/rca"
IMPACT_URL = "http://localhost:8001/api/ai/impact"

def test_impact_scenario(name, scenario, severity):
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=scenario, severity=severity)
    
    payload = {"machine_id": "M03", "telemetry": t.model_dump()}
    response = requests.post(ANOMALY_URL, json=payload)
    anomaly_result = response.json()
    
    rca_payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump(),
        "anomaly": anomaly_result,
        "maintenance_history": []
    }
    response_rca = requests.post(RCA_URL, json=rca_payload)
    rca_result = response_rca.json()

    impact_payload = {
        "machine_id": "M03",
        "telemetry": t.model_dump(),
        "anomaly": anomaly_result,
        "rca": rca_result
    }
    response_impact = requests.post(IMPACT_URL, json=impact_payload)
    impact_result = response_impact.json()

    print(f"\n================ {name.upper()} ================")
    print(f"Machine: M03")
    print(f"Scenario: {scenario}")
    print(f"Baseline Throughput: {impact_result['impact']['production']['baseline_throughput']}")
    print(f"Current Throughput: {impact_result['impact']['production']['current_throughput']}")
    print(f"Production Loss: {impact_result['impact']['production']['estimated_loss_per_hour']}")
    print(f"Loss Rate: {impact_result['impact']['production']['loss_rate']}")
    print(f"Downtime Risk: {impact_result['impact']['downtime']['risk_score']}")
    print(f"Projected Downtime: {impact_result['impact']['downtime']['projected_minutes']}")
    print(f"Quality Impact: {impact_result['impact']['quality']['impact']}")
    print(f"Affected Capacity: {impact_result['impact']['orders']['affected_capacity']}")
    print(f"Affected Orders: {impact_result['impact']['orders']['affected_orders']}")
    print(f"Impact Confidence: {impact_result['confidence']}")


if __name__ == "__main__":
    test_impact_scenario("NORMAL 1", NORMAL_01_STABLE_PRODUCTION, 0.0)
    test_impact_scenario("NORMAL 2", NORMAL_02_HIGH_DEMAND_STABLE, 0.0)
    test_impact_scenario("NORMAL 3", NORMAL_03_MINOR_VARIATION, 0.0)
    test_impact_scenario("DISRUPTION 1", DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    test_impact_scenario("DISRUPTION 2", DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    test_impact_scenario("DISRUPTION 3", DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
