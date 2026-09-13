"""
CAUSEN AI: Intelligent Industrial Decision Engine
Evaluates and compares recovery strategies across downtime, production loss,
scrap defect risk, and maintenance cost. Selects the globally optimal recovery action
with the lowest expected operational loss score.
"""

from typing import Dict, Any, List


class DecisionEngine:
    """
    Multi-criteria decision analysis engine for industrial recovery.
    """

    def __init__(self):
        pass

    def evaluate_and_recommend(
        self,
        machine_id: str,
        rca_result: Dict[str, Any],
        impact_result: Dict[str, Any],
        simulated_options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Rank recovery options and formulate optimal recommendation with confidence score.
        """
        # Sort strategies by lowest operational loss score
        ranked_options = sorted(simulated_options, key=lambda x: x["operational_loss_score"])
        best_option = ranked_options[0]

        # Calculate comparative advantage vs second-best option
        second_best = ranked_options[1]
        score_gap = second_best["operational_loss_score"] - best_option["operational_loss_score"]
        
        # Confidence score: base 85% + margin advantage
        confidence = min(96.0, round(85.0 + min(10.0, score_gap * 0.5), 1))

        # Build comprehensive rationale
        if best_option["action"] == "REROUTE_WORKLOAD":
            rationale = (
                f"Workload redistribution to {best_option.get('target_line', 'LINE-3')} produces the "
                f"lowest operational loss score ({best_option['operational_loss_score']} vs "
                f"{second_best['operational_loss_score']} for {second_best['name']}). It avoids "
                f"costly line halts by transferring active production to available parallel capacity, "
                f"limiting downtime to just {best_option['downtime_min']} minutes and production loss "
                f"to only {best_option['production_loss_units']} units while protecting downstream flow."
            )
        elif best_option["action"] == "STOP_MAINTAIN":
            rationale = (
                f"Immediate maintenance is required to prevent catastrophic component seizure. "
                f"While incurring {best_option['downtime_min']} min downtime, it halts the "
                f"escalating defect rate and prevents emergency repair costs."
            )
        else:
            rationale = (
                f"{best_option['name']} yields the lowest composite disruption score "
                f"({best_option['operational_loss_score']}) among all simulated alternatives."
            )

        # Build comparison summary matrix
        comparison_matrix = []
        for opt in ranked_options:
            is_best = (opt["option_id"] == best_option["option_id"])
            comparison_matrix.append({
                "option_id": opt["option_id"],
                "name": opt["name"],
                "action": opt["action"],
                "downtime_min": opt["downtime_min"],
                "production_loss_units": opt["production_loss_units"],
                "risk_level": opt["risk_level"],
                "maintenance_cost_usd": opt["maintenance_cost_usd"],
                "operational_loss_score": opt["operational_loss_score"],
                "is_recommended": is_best
            })

        return {
            "recommended_option_id": best_option["option_id"],
            "recommended_action": best_option["name"],
            "action_code": best_option["action"],
            "target_machine": best_option.get("target_machine"),
            "target_line": best_option.get("target_line"),
            "expected_loss_score": best_option["operational_loss_score"],
            "confidence": confidence,
            "reason": rationale,
            "details": best_option,
            "ranked_comparison": comparison_matrix
        }


def make_recovery_decision(
    machine_id: str,
    rca_result: Dict[str, Any],
    impact_result: Dict[str, Any],
    simulated_options: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Convenience wrapper."""
    engine = DecisionEngine()
    return engine.evaluate_and_recommend(machine_id, rca_result, impact_result, simulated_options)


if __name__ == "__main__":
    from src.recovery_simulation import run_recovery_simulation
    mock_rca = {"severity": "CRITICAL", "probable_root_cause": "Cooling System Degradation"}
    mock_impact = {"estimated_downtime_min": 35.0, "production_loss_units": 150}
    mock_peak = {"temperature": 71.0, "vibration": 4.8, "production_rate": 1040.0, "defect_rate": 3.2}
    sim_res = run_recovery_simulation("M03", mock_rca, mock_impact, mock_peak)
    decision = make_recovery_decision("M03", mock_rca, mock_impact, sim_res["options"])
    print("\n" + "="*50)
    print("           CAUSEN AI RECOMMENDATION")
    print("="*50)
    print(f"Recommended Action:   {decision['recommended_action']}")
    print(f"Confidence:           {decision['confidence']}%")
    print(f"Expected Loss Score:  {decision['expected_loss_score']}")
    print(f"\nReason:\n{decision['reason']}\n")
