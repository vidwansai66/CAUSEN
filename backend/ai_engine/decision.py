import logging
from typing import List, Dict, Any

from .models import (
    DecisionRequest,
    DecisionResult,
    DecisionDecision,
    RankedOption,
    RejectedAlternative,
    RecoverySimulationResult
)

logger = logging.getLogger(__name__)

def make_decision(request: DecisionRequest) -> DecisionResult:
    """
    Evaluates recovery options deterministically to recommend the best intervention based on safety and operational trade-offs.
    """
    # 1. Healthy Machine / Minor Variation Short-Circuit
    if request.anomaly.anomaly_score == 0.0 and request.impact.impact.downtime.risk_score < 0.1:
        return _build_no_action_response(
            request, 
            "Machine is operating within expected limits; intervention is not justified.",
            "NORMAL"
        )
        
    if request.anomaly.severity == "LOW":
        # Check if we have high impact risk despite low anomaly
        if request.impact.impact.downtime.risk_score < 0.3:
            return _build_no_action_response(
                request, 
                "Minor variation detected but operational risk is low. Aggressive intervention is not justified.",
                "LOW"
            )

    # 2. Score Options
    ranked_options = []
    assumptions = []
    
    # Extract baseline RCA confidence safely
    rca_conf = request.rca.probable_cause.confidence if hasattr(request.rca, "probable_cause") and hasattr(request.rca.probable_cause, "confidence") else getattr(request.rca, "confidence", 0.0)

    for option in request.recovery_options:
        score_details = _score_option(option, request, rca_conf)
        ranked_options.append(score_details)
        assumptions.extend(option.assumptions)
        
    if not ranked_options:
        return _build_no_action_response(request, "No recovery options provided.", request.anomaly.severity)

    # 3. Rank Options
    ranked_options.sort(key=lambda x: x["score"], reverse=True)
    
    # Assign ranks
    for i, opt in enumerate(ranked_options):
        opt["rank"] = i + 1
        
    top_option = ranked_options[0]
    
    # 4. No Action Fallback
    if top_option["score"] <= 0.0 or (top_option["action_id"] == "CONTINUE_UNCHECKED" and top_option["score"] < 0.2):
        if all(o["score"] <= 0.0 for o in ranked_options):
            return _build_no_action_response(
                request,
                "No modeled recovery action provides sufficient evidence of improvement. Escalation/manual assessment required.",
                request.anomaly.severity,
                rejected_actions=ranked_options
            )

    # 5. Ambiguity & Confidence Calculation
    decision_confidence = 0.8 # Base confidence
    if len(ranked_options) > 1:
        margin = ranked_options[0]["score"] - ranked_options[1]["score"]
        if margin < 0.05:
            decision_confidence -= 0.3
        elif margin < 0.15:
            decision_confidence -= 0.1
            
    # Penalize confidence if top option itself is low confidence
    decision_confidence = decision_confidence * top_option["confidence"]
    decision_confidence = round(max(0.0, min(1.0, decision_confidence)), 2)
    
    recommendation_text = top_option["reason"]
    if decision_confidence < 0.6:
        recommendation_text += " (Recommendation has low/moderate confidence because leading options have similar scores or low simulation confidence)."
        
    # 6. Build final components
    why_this_action = [top_option["reason"]]
    operational_tradeoffs = [top_option["production_tradeoff"]]
    evidence = [
        f"Initial anomaly severity was {request.anomaly.severity} (score: {request.anomaly.anomaly_score}).",
        f"Initial downtime risk was {request.impact.impact.downtime.risk_score}.",
        f"Selected action effectiveness: {top_option['effectiveness']}.",
        f"Simulated residual risk: {top_option['residual_risk']}."
    ]
    
    rejected = []
    for opt in ranked_options[1:]:
        reason = "Ranked lower due to inferior score."
        if opt["residual_risk"] == "CRITICAL" and top_option["residual_risk"] != "CRITICAL":
            reason = "Leaves critical residual risk."
        elif top_option["score"] - opt["score"] < 0.05:
            reason = "Option is viable but marginally less optimal."
        elif opt["action_id"] == "CONTINUE_UNCHECKED":
            reason = "Safety/risk reduction outweighs immediate production preservation."
        elif "100% loss" in opt["production_tradeoff"] and "100% loss" not in top_option["production_tradeoff"]:
             reason = "Unnecessary production halt when safer alternatives exist."
             
        rejected.append(RejectedAlternative(action_id=opt["action_id"], reason=reason))

    # Remove duplicates from assumptions while keeping order
    seen_assumptions = set()
    unique_assumptions = []
    for a in assumptions:
        if a not in seen_assumptions:
            unique_assumptions.append(a)
            seen_assumptions.add(a)

    return DecisionResult(
        machine_id=request.machine_id,
        decision=DecisionDecision(
            recommended_action=top_option["action_id"],
            recommendation=recommendation_text,
            decision_confidence=decision_confidence
        ),
        risk_level=request.anomaly.severity,
        ranked_options=[RankedOption(**opt) for opt in ranked_options],
        why_this_action=why_this_action,
        rejected_alternatives=rejected,
        operational_tradeoffs=operational_tradeoffs,
        evidence=evidence,
        assumptions=unique_assumptions
    )

def _score_option(option: RecoverySimulationResult, request: DecisionRequest, rca_conf: float) -> dict:
    """
    Deterministically scores a recovery option based on Safety (40%), Production (20%), 
    Effectiveness (20%), and Confidence (20%).
    """
    if option.action.action_id == "INVALID_ACTION":
        return _build_option_dict(option, 0.0, "UNKNOWN", "Unknown", "Unsupported action.")

    before = option.before
    after = option.after
    
    # 1. Risk Reduction
    # Anomaly score often increases during interventions because throughput drops to 0 (a production anomaly).
    # Therefore, downtime_risk is a purer measure of physical machine safety/stress reduction.
    anomaly_reduction = max(0.0, before.anomaly_score - after.anomaly_score)
    risk_reduction = max(0.0, before.downtime_risk - after.downtime_risk)
    
    # Weight physical downtime risk heavily over anomaly reduction to prevent production anomalies from masking safety improvements
    safety_score = (anomaly_reduction * 0.2) + (risk_reduction * 0.8)
    
    # 2. Production Preservation
    after_loss = after.production_loss_rate if after.production_loss_rate is not None else 0.0
    production_score = max(0.0, 1.0 - after_loss)
    
    # 3. Effectiveness & Confidence
    eff_score = option.recovery_effectiveness
    conf_score = (option.confidence * 0.5) + (rca_conf * 0.5)

    # 4. Dynamic Weighting: Safety Priority
    # If the machine is in critical danger, safety outweighs short-term production preservation.
    w_safety, w_prod, w_eff, w_conf = 0.4, 0.2, 0.2, 0.2
    
    if before.downtime_risk >= 0.9 or before.anomaly_score >= 0.9:
        w_safety = 0.55
        w_prod = 0.05 # Crush production preservation priority when safety is critical

    # Base formula
    score = (safety_score * w_safety) + (production_score * w_prod) + (eff_score * w_eff) + (conf_score * w_conf)
    
    # 5. Residual Risk Determination
    residual_risk = "LOW"
    if after.anomaly_score > 0.8 or after.downtime_risk > 0.8:
        residual_risk = "CRITICAL"
    elif after.anomaly_score > 0.5 or after.downtime_risk > 0.5:
        residual_risk = "MEDIUM"

    # 5. Penalties & Trade-offs
    tradeoff_desc = f"Maintains {round(production_score * 100)}% production capacity."
    
    if option.action.action_id == "CONTINUE_UNCHECKED":
        # Strongly penalize doing nothing if risk is high
        if before.anomaly_score > 0.8 or before.downtime_risk > 0.8:
            score -= 0.5
            tradeoff_desc = "Preserves current production but ignores critical risk."
        else:
            tradeoff_desc = "Preserves normal operation."
            
    elif option.action.action_id == "STOP_MAINTAIN":
        tradeoff_desc = "Halts production completely (100% immediate loss)."
        # If machine is not critical, penalize stopping it
        if before.anomaly_score < 0.5 and before.downtime_risk < 0.5:
            score -= 0.3
            
    elif option.action.action_id == "REROUTE_WORKLOAD":
        tradeoff_desc = "Reduces local throughput capacity to shift stress."
        
    elif option.action.action_id == "DERATE_SPEED":
        tradeoff_desc = "Reduces speed to mitigate stress at the cost of throughput."

    # Build Reason string
    reason = f"Provides a score of {round(score, 2)} with effectiveness {eff_score}."
    if residual_risk == "CRITICAL" and option.action.action_id != "CONTINUE_UNCHECKED":
        reason += " Note: Leaves machine in a critical state."
    if option.action.action_id == "STOP_MAINTAIN" and score > 0.5:
        reason = "Safety/risk reduction outweighs immediate production preservation under critical conditions."

    score = round(max(0.0, min(1.0, score)), 3)

    return _build_option_dict(option, score, residual_risk, tradeoff_desc, reason)

def _build_option_dict(option, score, residual, tradeoff, reason):
    return {
        "action_id": option.action.action_id,
        "rank": 0, # Placeholder
        "score": score,
        "effectiveness": option.recovery_effectiveness,
        "confidence": option.confidence,
        "residual_risk": residual,
        "production_tradeoff": tradeoff,
        "reason": reason
    }

def _build_no_action_response(request, recommendation: str, severity: str, rejected_actions: list = None) -> DecisionResult:
    rejected = []
    if rejected_actions:
        for opt in rejected_actions:
            rejected.append(RejectedAlternative(action_id=opt["action_id"], reason="Insufficient evidence of improvement."))
            
    return DecisionResult(
        machine_id=request.machine_id,
        decision=DecisionDecision(
            recommended_action="NO_ACTION",
            recommendation=recommendation,
            decision_confidence=1.0
        ),
        risk_level=severity,
        ranked_options=[],
        why_this_action=[recommendation],
        rejected_alternatives=rejected,
        operational_tradeoffs=["No immediate operational change."],
        evidence=["Anomaly score: " + str(request.anomaly.anomaly_score)],
        assumptions=["Machine state accurately reflects telemetry."]
    )
