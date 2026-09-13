import sys
import os
from typing import List, Dict, Any

from .models import (
    ImpactRequest, 
    ImpactResult, 
    ImpactDetails,
    ImpactProduction,
    ImpactDowntime,
    ImpactQuality,
    ImpactOrders,
    ImpactFinancial
)

# Import baseline configs to avoid duplicating it
SIM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "simulation"))
if SIM_PATH not in sys.path:
    sys.path.insert(0, SIM_PATH)

try:
    from src.config import MACHINES_CONFIG
except ImportError:
    MACHINES_CONFIG = {}

def predict_impact(request: ImpactRequest) -> ImpactResult:
    machine_id = request.machine_id
    telemetry = request.telemetry
    anomaly = request.anomaly
    rca = request.rca

    cfg = MACHINES_CONFIG.get(machine_id, {})
    baseline = cfg.get("baseline", {})
    
    # Fallback to telemetry values if baseline is totally missing for non-throughput metrics
    base_tput = baseline.get("throughput_uph", 1400.0) # we need a baseline to calculate loss, default to 1400 if missing config
    base_qual = baseline.get("defect_rate", telemetry.get("defect_rate", 0.3))
    base_temp = baseline.get("temperature", telemetry.get("temperature", 42.0))
    base_vib = baseline.get("vibration", telemetry.get("vibration", 1.2))

    current_tput = telemetry.get("throughput", None)
    current_qual = telemetry.get("defect_rate", base_qual)
    current_temp = telemetry.get("temperature", base_temp)
    current_vib = telemetry.get("vibration", base_vib)
    current_state = telemetry.get("state", "HEALTHY")

    # 1. Production Impact
    loss = None
    loss_rate = None
    estimated_loss_per_hour = None
    
    if current_tput is not None:
        loss = max(0.0, base_tput - current_tput)
        loss_rate = loss / base_tput if base_tput > 0 else 0.0
        estimated_loss_per_hour = loss

    production = ImpactProduction(
        baseline_throughput=base_tput,
        current_throughput=current_tput,
        loss_rate=round(loss_rate, 3) if loss_rate is not None else None,
        estimated_loss_per_hour=round(estimated_loss_per_hour, 1) if estimated_loss_per_hour is not None else None
    )

    # 2. Downtime Risk
    # Do not confuse risk with confirmed downtime
    observed_downtime = 0.0
    if current_tput == 0.0 and current_state == "CRITICAL":
        observed_downtime = 1.0 # arbitrary small number or just flag as down
        
    risk_score = 0.0
    if anomaly.is_anomaly:
        risk_score = anomaly.anomaly_score * 0.5
        
        # Increase risk based on specific evidence like heat or vibration
        # Cooling failure / excessive heat builds risk fast
        temp_dev = (current_temp - base_temp) / base_temp if base_temp > 0 else 0
        if temp_dev > 0.2:
            risk_score += min(0.3, temp_dev)
            
        vib_dev = (current_vib - base_vib) / base_vib if base_vib > 0 else 0
        if vib_dev > 0.5:
            risk_score += min(0.3, vib_dev * 0.5)
            
        risk_score += (rca.probable_cause.confidence * 0.2)
        
    risk_score = max(0.0, min(1.0, risk_score))
    
    projected_minutes = None

    downtime = ImpactDowntime(
        observed_minutes=observed_downtime,
        risk_score=round(risk_score, 2),
        projected_minutes=projected_minutes
    )

    # 3. Quality Impact
    qual_impact = "LOW"
    if current_qual > base_qual * 3.0:
        qual_impact = "HIGH"
    elif current_qual > base_qual * 1.5:
        qual_impact = "MEDIUM"
        
    quality = ImpactQuality(
        current_quality=current_qual,
        baseline_quality=base_qual,
        impact=qual_impact
    )

    # 4. Orders Impact
    # Assuming standard order size of 50 units (based on existing logic)
    affected_capacity = round(loss_rate, 3) if loss_rate is not None else 0.0
    affected_orders = None
    if estimated_loss_per_hour is not None:
        affected_orders = int(estimated_loss_per_hour / 50) if estimated_loss_per_hour > 0 else 0
    
    orders = ImpactOrders(
        affected_capacity=affected_capacity,
        affected_orders=affected_orders
    )

    # 5. Financial Impact
    # No reliable baseline cost exists, so do not fabricate
    financial = ImpactFinancial(
        estimated_loss=None,
        currency=None
    )

    # Construct Details
    details = ImpactDetails(
        production=production,
        downtime=downtime,
        quality=quality,
        orders=orders,
        financial=financial
    )

    # Confidence and Explanations
    evidence = []
    assumptions = []
    
    # Calculate Impact Confidence deterministically using multiple available factors
    # Base confidence starts high if everything is present
    confidence = 1.0
    
    if not cfg:
        confidence -= 0.15 # Baseline unavailable
        assumptions.append("Machine configuration not found. Baseline inferred from defaults/telemetry.")
        
    if current_tput is None:
        confidence -= 0.25 # Telemetry missing required metrics
        assumptions.append("Throughput telemetry is missing. Cannot evaluate loss.")
        
    if anomaly.is_anomaly:
        # Penalty if RCA confidence is weak, but not a linear copy
        if rca.probable_cause.confidence < 0.5:
            confidence -= 0.15
            
        # Penalty if anomaly score is low but RCA claims anomaly
        if anomaly.anomaly_score < 0.3:
            confidence -= 0.1
            
        # Boost confidence slightly if specific severe evidence aligns with impact
        if temp_dev > 0.2 or vib_dev > 0.2:
            confidence += 0.05
        
    confidence = round(max(0.1, min(1.0, confidence)), 2)

    # Generate Explanation
    if not anomaly.is_anomaly or anomaly.anomaly_score < 0.25:
        explanation = "Machine is operating within normal tolerances. No significant operational impact expected."
    else:
        primary = rca.probable_cause.name
        
        explanation_parts = []
        if loss_rate is not None and loss_rate > 0.1:
            explanation_parts.append(f"Throughput is {round(loss_rate*100, 1)}% below baseline, resulting in a loss of {round(estimated_loss_per_hour, 1)} units/hour.")
            evidence.append(f"Throughput deviation: -{round(loss_rate*100, 1)}%")
        elif loss_rate is None:
            explanation_parts.append(f"Throughput data unavailable, production loss cannot be calculated.")
            
        if risk_score > 0.5:
            explanation_parts.append(f"High risk of downtime ({round(risk_score*100)}%) driven by {primary}.")
            evidence.append(f"Downtime risk score: {round(risk_score, 2)}")
            
        if qual_impact in ["MEDIUM", "HIGH"]:
            explanation_parts.append(f"Quality defect rate is elevated ({qual_impact} impact).")
            evidence.append(f"Defect rate: {round(current_qual, 2)}% vs baseline {round(base_qual, 2)}%")
            
        if not explanation_parts:
            explanation_parts.append(f"Anomaly detected but with minimal immediate production or quality impact. Driven by {primary}.")
            
        explanation = " ".join(explanation_parts)

    if projected_minutes is None:
        assumptions.append("Projected downtime unavailable: insufficient historical duration/trend evidence.")
        
    assumptions.append("Order impact assumes standard order size of 50 units.")
    assumptions.append("Financial impact omitted due to unavailable cost baseline.")

    return ImpactResult(
        machine_id=machine_id,
        impact=details,
        confidence=confidence,
        evidence=evidence,
        assumptions=assumptions,
        explanation=explanation
    )
