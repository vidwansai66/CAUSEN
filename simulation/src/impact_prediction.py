"""
CAUSEN AI: Operational Impact Prediction Engine
Estimates production loss, downtime, scrap defect increases, downstream delay,
and calculates a transparent Composite Operational Loss Score (0-100).
"""

from typing import Dict, Any
from src.config import MACHINES_CONFIG


class OperationalImpactPredictor:
    """
    Computes business and operational fallout metrics for machine anomalies.
    """

    def __init__(self, buffer_capacity_minutes: float = 10.0):
        self.buffer_capacity_minutes = buffer_capacity_minutes

    def predict(
        self,
        machine_id: str,
        rca_result: Dict[str, Any],
        peak_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate quantitative impact metrics based on machine role and failure severity.
        """
        cfg = MACHINES_CONFIG.get(machine_id, MACHINES_CONFIG["M03"])
        nominal_uph = cfg["baseline"]["throughput_uph"]
        nominal_per_min = nominal_uph / 60.0
        baseline_defect_pct = cfg["baseline"]["defect_rate"]

        current_prod = peak_record.get("production_rate", nominal_uph * 0.75)
        current_defect_pct = peak_record.get("defect_rate", baseline_defect_pct)
        severity = rca_result.get("severity", "HIGH")
        cause = rca_result.get("probable_root_cause", "")

        # 1. Estimated Downtime (minutes) based on failure type and severity
        if "Cooling" in cause:
            est_downtime = 35.0 if severity == "CRITICAL" else 20.0
        elif "Bearing" in cause:
            est_downtime = 45.0 if severity == "CRITICAL" else 25.0
        elif "Motor" in cause:
            est_downtime = 60.0 if severity == "CRITICAL" else 30.0
        elif "Misalignment" in cause:
            est_downtime = 15.0
        elif "Material" in cause:
            est_downtime = 10.0
        else:
            est_downtime = 30.0

        # 2. Estimated Production Loss (units)
        # Production lost during stoppage + production throttled during degraded run (30 min window)
        degraded_deficit = max(0.0, (nominal_uph - current_prod) * (30.0 / 60.0))
        downtime_deficit = nominal_per_min * est_downtime
        total_prod_loss_units = round(degraded_deficit + downtime_deficit, 0)

        # 3. Expected Defect Increase
        defect_increase_pct = max(0.0, current_defect_pct - baseline_defect_pct)
        # Projected scrap units during the incident window
        units_produced = (current_prod * 0.5)
        estimated_scrap_units = round(units_produced * (current_defect_pct / 100.0), 0)

        # 4. Downstream Delay (minutes)
        # Buffers absorb up to buffer_capacity_minutes; surplus translates to line starvation
        downstream_delay = max(0.0, est_downtime - self.buffer_capacity_minutes)

        # 5. Composite Operational Loss Score (0 to 100)
        # Weights: Downtime (30%), Production Loss (30%), Defect Risk (20%), Downstream Disruption (20%)
        norm_downtime = min(100.0, (est_downtime / 60.0) * 100.0)
        norm_loss = min(100.0, (total_prod_loss_units / 500.0) * 100.0)
        norm_defect = min(100.0, (defect_increase_pct / 5.0) * 100.0)
        norm_delay = min(100.0, (downstream_delay / 45.0) * 100.0)

        loss_score = round(
            0.30 * norm_downtime +
            0.30 * norm_loss +
            0.20 * norm_defect +
            0.20 * norm_delay,
            1
        )

        if loss_score < 30:
            category = "Low"
        elif loss_score < 55:
            category = "Medium"
        elif loss_score < 80:
            category = "High"
        else:
            category = "Critical"

        formulas_explanation = {
            "downtime_formula": f"Estimated repair window based on {cause} ({severity} severity)",
            "production_loss_formula": (
                f"Deficit during degraded operation ({round(degraded_deficit)} units) + "
                f"Deficit during stoppage ({round(downtime_deficit)} units) = {int(total_prod_loss_units)} units"
            ),
            "defect_formula": f"Observed ({current_defect_pct}%) - Baseline ({baseline_defect_pct}%) = +{round(defect_increase_pct, 2)}%",
            "downstream_formula": f"max(0, Downtime ({est_downtime} min) - Buffer ({self.buffer_capacity_minutes} min)) = {downstream_delay} min",
            "loss_score_formula": "0.30*(Norm Downtime) + 0.30*(Norm Prod Loss) + 0.20*(Norm Defect) + 0.20*(Norm Downstream Delay)"
        }

        return {
            "machine_id": machine_id,
            "machine_name": cfg["name"],
            "estimated_downtime_min": est_downtime,
            "production_loss_units": int(total_prod_loss_units),
            "expected_defect_increase_pct": round(defect_increase_pct, 2),
            "estimated_scrap_units": int(estimated_scrap_units),
            "downstream_delay_min": round(downstream_delay, 1),
            "operational_loss_score": loss_score,
            "loss_category": category,
            "formulas": formulas_explanation
        }


def predict_operational_impact(rca_result: Dict[str, Any], peak_record: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper."""
    predictor = OperationalImpactPredictor()
    machine_id = rca_result.get("machine_id", "M03")
    return predictor.predict(machine_id, rca_result, peak_record)


if __name__ == "__main__":
    mock_rca = {
        "machine_id": "M03",
        "severity": "CRITICAL",
        "probable_root_cause": "Cooling System Degradation & Thermal Stress"
    }
    mock_peak = {
        "temperature": 71.0,
        "vibration": 4.8,
        "production_rate": 1040.0,
        "defect_rate": 3.2
    }
    impact = predict_operational_impact(mock_rca, mock_peak)
    print("\n--- OPERATIONAL IMPACT PREDICTION ---")
    print(f"Machine:                 {impact['machine_name']}")
    print(f"Estimated Downtime:      {impact['estimated_downtime_min']} minutes")
    print(f"Production Loss:         {impact['production_loss_units']} units")
    print(f"Expected Defect Incr:    +{impact['expected_defect_increase_pct']}%")
    print(f"Downstream Delay:        {impact['downstream_delay_min']} minutes")
    print(f"Operational Loss Score:  {impact['operational_loss_score']} ({impact['loss_category']})")
