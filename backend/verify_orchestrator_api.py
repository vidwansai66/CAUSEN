import requests
import time
from simulation.src.scenario_engine import generate_telemetry, DISRUPTION_01_COOLING_SYSTEM_DEGRADATION
import numpy as np

rng = np.random.default_rng(42)
t = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
data = {
    "machine_id": "M03",
    "telemetry": t.model_dump()
}

res = requests.post("http://127.0.0.1:8001/api/ai/analyze", json=data)
if res.status_code == 200:
    res_json = res.json()
    print("SUCCESS: 200 OK")
    print("Decision:", res_json["decision"]["decision"]["recommended_action"])
else:
    print("ERROR:", res.status_code, res.text)

