import json
from fastapi.testclient import TestClient
import os
import sys

BACKEND_PATH = os.path.abspath(os.path.dirname(__file__))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_PATH, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from simulation.src.scenario_engine import (
    generate_telemetry,
    NORMAL_01_STABLE_PRODUCTION,
    NORMAL_03_MINOR_VARIATION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

client = TestClient(app)

import numpy as np

def run_decision_pipeline(scenario_name, severity=1.0):
    print(f"\n==================================================")
    print(f"TESTING PIPELINE FOR: {scenario_name}")
    print(f"==================================================")
    
    # 1. Telemetry
    rng = np.random.default_rng(42)
    telemetry = generate_telemetry("M03", 0, rng, active_scenario=scenario_name, severity=severity).model_dump()
    
    # 2. Anomaly
    res_anomaly = client.post("/api/ai/anomaly", json={
        "machine_id": "M03",
        "telemetry": telemetry
    })
    anomaly = res_anomaly.json()
    
    # 3. RCA
    res_rca = client.post("/api/ai/rca", json={
        "machine_id": "M03",
        "telemetry": telemetry,
        "anomaly": anomaly
    })
    rca = res_rca.json()
    
    # 4. Impact
    res_impact = client.post("/api/ai/impact", json={
        "machine_id": "M03",
        "telemetry": telemetry,
        "anomaly": anomaly,
        "rca": rca
    })
    impact = res_impact.json()
    
    # 5. What-if Options
    options = []
    actions = [
        {"action_id": "STOP_MAINTAIN", "name": "Stop and Maintain", "description": ""},
        {"action_id": "DERATE_SPEED", "name": "Derate Speed", "description": ""},
        {"action_id": "REROUTE_WORKLOAD", "name": "Reroute Workload", "description": ""},
        {"action_id": "CONTINUE_UNCHECKED", "name": "Continue Unchecked", "description": ""}
    ]
    for action in actions:
        res_rec = client.post("/api/ai/recovery/simulate", json={
            "machine_id": "M03",
            "telemetry": telemetry,
            "anomaly": anomaly,
            "rca": rca,
            "impact": impact,
            "action": action
        })
        options.append(res_rec.json())
        
    # 6. Decision
    res_dec = client.post("/api/ai/decision", json={
        "machine_id": "M03",
        "telemetry": telemetry,
        "anomaly": anomaly,
        "rca": rca,
        "impact": impact,
        "recovery_options": options
    })
    dec = res_dec.json()
    
    # Print Results
    print(f"\nCurrent Machine State:")
    print(f"- anomaly: {anomaly['severity']}")
    print(f"- anomaly_score: {anomaly['anomaly_score']}")
    
    impact_downtime = impact['impact']['downtime']
    impact_prod = impact['impact']['production']
    print(f"- production loss: {round((impact_prod['loss_rate'] or 0.0) * 100, 2)}%")
    print(f"- downtime risk: {impact_downtime['risk_score']}")
    print(f"- RCA confidence: {rca.get('probable_cause', {}).get('confidence', 0.0)}")
    
    print("\nDecision Results:")
    print(f"Recommended Action : {dec['decision']['recommended_action']}")
    print(f"Decision Confidence: {dec['decision']['decision_confidence']}")
    print(f"Risk Level         : {dec['risk_level']}")
    
    print(f"\nWhy this action:")
    for w in dec['why_this_action']:
        print(f"  - {w}")
        
    print("\nRanked Options:")
    print(f"{'Rank':<5} | {'Action':<20} | {'Score':<6} | {'Eff':<4} | {'Res.Risk':<10} | {'Trade-off':<40} | {'Reason'}")
    print("-" * 140)
    for opt in dec['ranked_options']:
        print(f"{opt['rank']:<5} | {opt['action_id']:<20} | {opt['score']:<6} | {opt['effectiveness']:<4} | {opt['residual_risk']:<10} | {opt['production_tradeoff']:<40} | {opt['reason']}")

if __name__ == "__main__":
    run_decision_pipeline(NORMAL_01_STABLE_PRODUCTION, 0.0)
    run_decision_pipeline(NORMAL_03_MINOR_VARIATION, 0.5)
    run_decision_pipeline(DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, 1.0)
    run_decision_pipeline(DISRUPTION_02_BEARING_DEGRADATION, 1.0)
    run_decision_pipeline(DISRUPTION_03_THROUGHPUT_DEGRADATION, 1.0)
    
    print("\nTests complete.")
