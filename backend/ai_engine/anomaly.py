import sys
import os

# Ensure simulation can be imported
SIM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "simulation"))
if SIM_PATH not in sys.path:
    sys.path.insert(0, SIM_PATH)

from src.config import MACHINES_CONFIG
from .models import SignalEvidence, AnomalyResult, AnomalyRequest

def score_signal(name: str, val: float, base: float, tol_up: float, tol_down: float, max_dev_up: float, max_dev_down: float) -> SignalEvidence:
    """
    Normalizes a signal deviation into a 0.0 - 1.0 contribution score.
    Values within the tolerance band [base - tol_down, base + tol_up] score 0.0.
    """
    contribution = 0.0
    direction = "NORMAL"
    
    if val > base + tol_up:
        excess = val - (base + tol_up)
        contribution = min(1.0, excess / max_dev_up) if max_dev_up > 0 else 0.0
        direction = "HIGH"
    elif val < base - tol_down:
        deficit = (base - tol_down) - val
        contribution = min(1.0, deficit / max_dev_down) if max_dev_down > 0 else 0.0
        direction = "LOW"
        
    dev_pct = ((val - base) / base) * 100.0 if base != 0 else 0.0
    
    return SignalEvidence(
        name=name,
        baseline=base,
        current=round(val, 2),
        deviation_percent=round(dev_pct, 1),
        direction=direction,
        contribution=round(contribution, 3)
    )

def map_severity(score: float) -> str:
    if score < 0.25:
        return "NORMAL"
    elif score < 0.50:
        return "LOW"
    elif score < 0.75:
        return "MEDIUM"
    elif score < 0.90:
        return "HIGH"
    else:
        return "CRITICAL"

def detect_anomalies(request: AnomalyRequest) -> AnomalyResult:
    machine_id = request.machine_id
    telemetry = request.telemetry
    
    if machine_id not in MACHINES_CONFIG:
        raise ValueError(f"Machine {machine_id} not found in configuration.")
        
    baseline = MACHINES_CONFIG[machine_id]["baseline"]
    
    signals = []
    
    # 1. Temperature
    if "temperature" in telemetry:
        signals.append(score_signal(
            "temperature", telemetry["temperature"], baseline["temperature"],
            tol_up=6.0, tol_down=4.0, max_dev_up=25.0, max_dev_down=10.0
        ))
        
    # 2. Vibration
    if "vibration" in telemetry:
        signals.append(score_signal(
            "vibration", telemetry["vibration"], baseline["vibration"],
            tol_up=0.5, tol_down=0.5, max_dev_up=4.0, max_dev_down=1.0
        ))
        
    # 3. Throughput
    # Throughput is usually called "throughput" or "production_rate"
    tput_val = telemetry.get("throughput", telemetry.get("production_rate"))
    if tput_val is not None:
        signals.append(score_signal(
            "throughput", tput_val, baseline["throughput_uph"],
            tol_up=200.0, tol_down=150.0, max_dev_up=500.0, max_dev_down=800.0
        ))
        
    # 4. Defect Rate
    if "defect_rate" in telemetry:
        signals.append(score_signal(
            "defect_rate", telemetry["defect_rate"], baseline["defect_rate"],
            tol_up=0.7, tol_down=0.3, max_dev_up=3.0, max_dev_down=1.0
        ))
        
    # 5. Cycle Time
    if "cycle_time" in telemetry:
        signals.append(score_signal(
            "cycle_time", telemetry["cycle_time"], baseline["cycle_time"],
            tol_up=5.0, tol_down=5.0, max_dev_up=60.0, max_dev_down=10.0
        ))

    # Aggregation Method: Maximum Signal Score (L-infinity norm)
    # Rationale: In industrial machinery, a single critically failing component 
    # (e.g., severe vibration) is enough to cause a catastrophic breakdown, even if 
    # all other metrics (temperature, throughput) are perfectly normal. 
    # Averaging the scores would dilute a severe single-signal anomaly. 
    # Taking the maximum ensures the system severity always matches its most critical fault.
    
    anomaly_score = 0.0
    anomalous_signals = []
    
    for sig in signals:
        if sig.contribution > 0:
            anomalous_signals.append(sig)
        if sig.contribution > anomaly_score:
            anomaly_score = sig.contribution
            
    is_anomaly = anomaly_score >= 0.25
    severity = map_severity(anomaly_score)
    
    if not is_anomaly:
        summary = "Machine is operating within normal healthy tolerances."
    else:
        # Sort anomalous signals by contribution for the summary
        anomalous_signals.sort(key=lambda x: x.contribution, reverse=True)
        primary_sig = anomalous_signals[0].name
        summary = f"Anomaly detected. Primary contributor is {primary_sig} with a {anomalous_signals[0].deviation_percent}% deviation."

    return AnomalyResult(
        machine_id=machine_id,
        timestamp=telemetry.get("timestamp", ""),
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        severity=severity,
        signals=signals,
        summary=summary
    )
