import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app

client = TestClient(app)

def test_valid_request_healthy():
    payload = {
        "machine_id": "M03",
        "telemetry": {
            "temperature": 45.0,
            "vibration": 1.2,
            "throughput": 1400.0,
            "power_consumption": 18.0,
            "defect_rate": 0.5
        }
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "M03"
    assert data["anomaly"]["severity"] == "NORMAL"
    assert data["decision"]["decision"]["recommended_action"] == "NO_ACTION"
    assert data["decision"]["decision"]["decision_confidence"] == 1.0

def test_valid_request_severe_disruption():
    payload = {
        "machine_id": "M03",
        "telemetry": {
            "temperature": 75.0,
            "vibration": 3.5,
            "throughput": 1050.0,
            "power_consumption": 24.0,
            "defect_rate": 1.8
        }
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["anomaly"]["severity"] == "CRITICAL"
    assert data["decision"]["decision"]["recommended_action"] in ["STOP_MAINTAIN", "DERATE_SPEED", "REROUTE_WORKLOAD"]

def test_missing_machine_id():
    payload = {
        "telemetry": {
            "temperature": 45.0
        }
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 422

def test_missing_telemetry():
    payload = {
        "machine_id": "M03"
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 422

def test_empty_telemetry():
    payload = {
        "machine_id": "M03",
        "telemetry": {}
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 400

def test_malformed_telemetry():
    payload = {
        "machine_id": "M03",
        "telemetry": "this is a string, not a dict"
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 422

def test_deterministic_repeatability():
    payload = {
        "machine_id": "M03",
        "telemetry": {
            "temperature": 50.0,
            "vibration": 2.0,
            "throughput": 1300.0,
            "power_consumption": 20.0,
            "defect_rate": 1.0
        }
    }
    res1 = client.post("/api/ai/analyze", json=payload).json()
    res2 = client.post("/api/ai/analyze", json=payload).json()
    
    # Exclude timestamps
    res1["anomaly"].pop("timestamp", None)
    res2["anomaly"].pop("timestamp", None)
    
    assert res1 == res2

def test_no_side_effects():
    # Capture simulator state
    state1 = client.get("/api/state").json()
    
    # Run analysis
    payload = {
        "machine_id": "M03",
        "telemetry": {
            "temperature": 85.0,
            "vibration": 5.0,
            "throughput": 500.0,
            "power_consumption": 30.0,
            "defect_rate": 5.0
        }
    }
    res = client.post("/api/ai/analyze", json=payload)
    assert res.status_code == 200
    
    # Capture simulator state again
    state2 = client.get("/api/state").json()
    
    assert state1["demoState"] == state2["demoState"]

def test_complete_response_schema():
    payload = {
        "machine_id": "M03",
        "telemetry": {
            "temperature": 45.0,
            "vibration": 1.2,
            "throughput": 1400.0,
            "power_consumption": 18.0,
            "defect_rate": 0.5
        }
    }
    response = client.post("/api/ai/analyze", json=payload)
    data = response.json()
    assert "anomaly" in data
    assert "rca" in data
    assert "impact" in data
    assert "recovery_simulations" in data
    assert "decision" in data
    
    # Machine-readable action verification
    action = data["decision"]["decision"]["recommended_action"]
    valid_actions = ["NO_ACTION", "STOP_MAINTAIN", "DERATE_SPEED", "REROUTE_WORKLOAD", "CONTINUE_UNCHECKED"]
    assert action in valid_actions

