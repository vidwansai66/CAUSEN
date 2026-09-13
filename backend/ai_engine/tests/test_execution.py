import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app
from simulator_bridge import bridge

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_bridge():
    bridge.reset()
    yield
    bridge.reset()

def test_execute_invalid_action():
    payload = {
        "machine_id": "M03",
        "action_id": "INVALID_ACTION_ID"
    }
    response = client.post("/api/recovery/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "INVALID_ACTION"
    assert data["state_changed"] is False

def test_execute_missing_fields():
    payload = {
        "machine_id": "M03"
    }
    response = client.post("/api/recovery/execute", json=payload)
    assert response.status_code == 422

def test_execute_no_action():
    bridge.inject_fault("M03")
    payload = {
        "machine_id": "M03",
        "action_id": "NO_ACTION"
    }
    response = client.post("/api/recovery/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "NO_ACTION"
    assert data["state_changed"] is False

def test_execute_valid_action():
    bridge.inject_fault("M03")
    bridge.tick()
    payload = {
        "machine_id": "M03",
        "action_id": "STOP_MAINTAIN"
    }
    response = client.post("/api/recovery/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "EXECUTED"
    assert data["state_changed"] is True
    assert data["resulting_state"] == "RECOVERY"

def test_separation_analysis_vs_execution():
    bridge.inject_fault("M03")
    bridge.tick()
    
    # 1. Capture simulator state
    state1 = client.get("/api/state").json()
    
    # 2. POST /api/ai/analyze
    telemetry = bridge.machines["M03"].model_dump()
    analyze_payload = {
        "machine_id": "M03",
        "telemetry": telemetry
    }
    analyze_resp = client.post("/api/ai/analyze", json=analyze_payload)
    assert analyze_resp.status_code == 200
    
    # 3. Capture state. ASSERT No mutation.
    state2 = client.get("/api/state").json()
    assert state1["demoState"] == state2["demoState"]
    assert bridge.recovery_active is False
    
    # 4. Run what-if recovery simulation.
    anomaly = analyze_resp.json()["anomaly"]
    rca = analyze_resp.json()["rca"]
    impact = analyze_resp.json()["impact"]
    recovery_payload = {
        "machine_id": "M03",
        "telemetry": telemetry,
        "anomaly": anomaly,
        "rca": rca,
        "impact": impact,
        "action": {
            "action_id": "STOP_MAINTAIN",
            "name": "Stop and Maintain",
            "description": "Stop machine"
        }
    }
    sim_resp = client.post("/api/ai/recovery/simulate", json=recovery_payload)
    assert sim_resp.status_code == 200
    
    # 5. Capture state. ASSERT No mutation.
    state3 = client.get("/api/state").json()
    assert state2["demoState"] == state3["demoState"]
    assert bridge.recovery_active is False
    
    # 6. POST /api/recovery/execute with explicit action.
    execute_payload = {
        "machine_id": "M03",
        "action_id": "STOP_MAINTAIN"
    }
    execute_resp = client.post("/api/recovery/execute", json=execute_payload)
    assert execute_resp.status_code == 200
    
    # 7. Capture state. ASSERT Expected intentional mutation occurred.
    state4 = client.get("/api/state").json()
    assert state4["demoState"] == "RECOVERY"
    assert bridge.recovery_active is True
