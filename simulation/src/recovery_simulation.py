"""
CAUSEN AI: What-If Recovery Simulation Engine
Simulates 4 distinct operational recovery strategies for detected anomalies.
Computes downtime, production loss, scrap defect risk, maintenance expense,
and composite operational loss scores.
Also models closed-loop recovery trajectories returning machines to HEALTHY status.
"""

from typing import Dict, Any, List
from src.config import MACHINES_CONFIG, REROUTE_TARGET_MACHINE, REROUTE_TARGET_LINE


class RecoverySimulator:
    """
    Evaluates recovery strategies and models closed-loop dynamic stabilization.
    """

    def __init__(self):
        pass

    def simulate_options(
        self,
        machine_id: str,
        rca_result: Dict[str, Any],
        impact_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Simulate the 4 core industrial recovery strategies:
        - Option 1: Immediate Maintenance (Stop Machine)
        - Option 2: Reduce Machine Speed (Derate Speed)
        - Option 3: Workload Redistribution (Reroute to Parallel Line)
        - Option 4: Continue Production Without Intervention (Ignore Anomaly)
        """
        cfg = MACHINES_CONFIG.get(machine_id, MACHINES_CONFIG["M03"])
        nominal_uph = cfg["baseline"]["throughput_uph"]
        severity = rca_result.get("severity", "HIGH")
        cause = rca_result.get("probable_root_cause", "Anomaly")

        # --- OPTION 1: Immediate Maintenance ---
        # Stop machine now, execute targeted component repair
        downtime_opt1 = 30.0 if severity == "CRITICAL" else 20.0
        prod_loss_opt1 = round((downtime_opt1 / 60.0) * nominal_uph, 0)
        downstream_delay_opt1 = max(0.0, downtime_opt1 - 10.0)
        maint_cost_opt1 = 450.0  # Planned urgent repair parts & labor
        loss_score_opt1 = round(
            0.30 * min(100.0, (downtime_opt1 / 60.0) * 100.0) +
            0.30 * min(100.0, (prod_loss_opt1 / 400.0) * 100.0) +
            0.20 * 10.0 +  # Low defect risk
            0.20 * min(100.0, (downstream_delay_opt1 / 30.0) * 100.0),
            1
        )

        # --- OPTION 2: Reduce Machine Speed ---
        # Throttle to 55-60% speed, reduce mechanical heat/stress, continue running
        downtime_opt2 = 10.0  # Parameter adjustment & calibration stop
        # Runs at 60% capacity for 2 hours while technician monitors
        derated_loss = (nominal_uph * 0.40) * 2.0
        prod_loss_opt2 = round(((downtime_opt2 / 60.0) * nominal_uph) + derated_loss, 0)
        downstream_delay_opt2 = 10.0
        maint_cost_opt2 = 180.0
        loss_score_opt2 = round(
            0.30 * min(100.0, (downtime_opt2 / 60.0) * 100.0) +
            0.30 * min(100.0, (prod_loss_opt2 / 400.0) * 100.0) +
            0.20 * 35.0 +  # Medium defect risk
            0.20 * min(100.0, (downstream_delay_opt2 / 30.0) * 100.0),
            1
        )

        # --- OPTION 3: Workload Redistribution (Flagship Recommendation) ---
        # Switchover order queue from M03 (LINE-2) to M07 (LINE-3)
        downtime_opt3 = 5.0   # Quick software/PLC routing switch
        prod_loss_opt3 = round((downtime_opt3 / 60.0) * nominal_uph * 0.8, 0)  # ~35-40 units
        downstream_delay_opt3 = 5.0
        maint_cost_opt3 = 80.0   # Route reconfiguration overhead
        loss_score_opt3 = round(
            0.30 * min(100.0, (downtime_opt3 / 60.0) * 100.0) +
            0.30 * min(100.0, (prod_loss_opt3 / 400.0) * 100.0) +
            0.20 * 8.0 +   # Very low defect risk on target machine
            0.20 * min(100.0, (downstream_delay_opt3 / 30.0) * 100.0),
            1
        )

        # --- OPTION 4: Continue Production Without Intervention (Ignore Anomaly) ---
        # Run until catastrophic failure
        downtime_opt4 = 180.0  # Catastrophic seizure requires full disassembly & rebuild
        prod_loss_opt4 = round(nominal_uph * 2.5, 0)  # Massive unit shortfall
        downstream_delay_opt4 = 85.0
        maint_cost_opt4 = 2800.0  # Emergency component destruction, overtime technicians
        loss_score_opt4 = 95.0

        options = [
            {
                "option_id": 1,
                "name": "Immediate Maintenance",
                "action": "STOP_MAINTAIN",
                "description": "Stop machine immediately and perform targeted component maintenance.",
                "downtime_min": downtime_opt1,
                "production_loss_units": int(prod_loss_opt1),
                "risk_level": "Low",
                "defect_risk_pct": 0.5,
                "maintenance_cost_usd": maint_cost_opt1,
                "downstream_delay_min": downstream_delay_opt1,
                "operational_loss_score": loss_score_opt1,
                "tradeoff": "Eliminates catastrophic failure risk, but causes 30 min stoppage."
            },
            {
                "option_id": 2,
                "name": "Reduce Machine Speed",
                "action": "DERATE_SPEED",
                "description": "Reduce machine operating speed by 40% to alleviate thermal/vibration stress.",
                "downtime_min": downtime_opt2,
                "production_loss_units": int(prod_loss_opt2),
                "risk_level": "Medium",
                "defect_risk_pct": 1.6,
                "maintenance_cost_usd": maint_cost_opt2,
                "downstream_delay_min": downstream_delay_opt2,
                "operational_loss_score": loss_score_opt2,
                "tradeoff": "Minimizes stoppage time, but results in prolonged throughput drag."
            },
            {
                "option_id": 3,
                "name": "Workload Redistribution",
                "action": "REROUTE_WORKLOAD",
                "target_machine": REROUTE_TARGET_MACHINE,
                "target_line": REROUTE_TARGET_LINE,
                "description": (
                    f"Reroute 80% of active order queue to backup line ({REROUTE_TARGET_LINE} / "
                    f"{MACHINES_CONFIG[REROUTE_TARGET_MACHINE]['role']})."
                ),
                "downtime_min": downtime_opt3,
                "production_loss_units": int(prod_loss_opt3),
                "risk_level": "Low",
                "defect_risk_pct": 0.4,
                "maintenance_cost_usd": maint_cost_opt3,
                "downstream_delay_min": downstream_delay_opt3,
                "operational_loss_score": loss_score_opt3,
                "tradeoff": "Lowest operational disruption and downtime; requires parallel line buffer capacity."
            },
            {
                "option_id": 4,
                "name": "Ignore Anomaly",
                "action": "CONTINUE_UNCHECKED",
                "description": "Continue production without intervention and run until failure.",
                "downtime_min": downtime_opt4,
                "production_loss_units": int(prod_loss_opt4),
                "risk_level": "Very High",
                "defect_risk_pct": 6.8,
                "maintenance_cost_usd": maint_cost_opt4,
                "downstream_delay_min": downstream_delay_opt4,
                "operational_loss_score": loss_score_opt4,
                "tradeoff": "Guaranteed catastrophic failure, massive downstream starvation, and high scrap rate."
            }
        ]

        return options

    def simulate_recovery_trajectory(
        self,
        machine_id: str,
        selected_option: Dict[str, Any],
        incident_readings: Dict[str, float],
        steps: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Simulate the closed-loop recovery trajectory over time (Page 5 of Engineer Handoff).
        
        Example M03 recovery trajectory:
        - Temperature: 71°C -> 67 -> 60 -> 51 -> 44 -> ~43°C
        - Vibration: 4.8 mm/s -> 4.1 -> 3.5 -> 2.3 -> 1.7 -> ~1.3 mm/s
        - Cycle time: 61s -> 58 -> 54 -> 49 -> 46 -> ~45s
        - Throughput: 1040 u/h -> 1110 -> 1190 -> 1270 -> 1380 -> ~1400 u/h
        - Quality: 96.8% -> 97.5 -> 98.2 -> 98.9 -> 99.4 -> ~99.7%
        """
        cfg = MACHINES_CONFIG.get(machine_id, MACHINES_CONFIG["M03"])
        target = cfg["baseline"]

        init_temp = incident_readings.get("temperature", 71.0)
        init_vib = incident_readings.get("vibration", 4.8)
        init_prod = incident_readings.get("production_rate", 1040.0)
        init_defect = incident_readings.get("defect_rate", 3.2)

        target_temp = target["temperature"]
        target_vib = target["vibration"]
        target_prod = target["throughput_uph"]
        target_defect = target["defect_rate"]

        trajectory = []
        for i in range(steps):
            ratio = i / (steps - 1)  # 0.0 to 1.0
            # Exponential decay towards baseline
            decay = 1.0 - (1.0 - ratio) ** 1.8
            
            cur_temp = round(init_temp - (init_temp - target_temp) * decay, 1)
            cur_vib = round(init_vib - (init_vib - target_vib) * decay, 2)
            cur_prod = round(init_prod + (target_prod - init_prod) * decay, 0)
            cur_defect = round(init_defect - (init_defect - target_defect) * decay, 2)
            cur_qual = round(100.0 - cur_defect, 1)

            if i == 0:
                state = "CRITICAL"
                action_status = "COMMAND_ISSUED"
            elif i < steps - 1:
                state = "RECOVERING"
                action_status = "EXECUTING"
            else:
                state = "RECOVERED/HEALTHY"
                action_status = "COMPLETED"

            trajectory.append({
                "stage_index": i + 1,
                "state": state,
                "action_status": action_status,
                "temperature": cur_temp,
                "vibration": cur_vib,
                "production_rate": cur_prod,
                "quality_pct": cur_qual,
                "defect_rate": cur_defect
            })

        return trajectory


def run_recovery_simulation(
    machine_id: str,
    rca_result: Dict[str, Any],
    impact_result: Dict[str, Any],
    peak_record: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience runner."""
    sim = RecoverySimulator()
    options = sim.simulate_options(machine_id, rca_result, impact_result)
    # Target option 3 for trajectory simulation
    traj = sim.simulate_recovery_trajectory(machine_id, options[2], peak_record)
    return {
        "options": options,
        "recovery_trajectory": traj
    }


if __name__ == "__main__":
    mock_rca = {"severity": "CRITICAL", "probable_root_cause": "Cooling System Degradation"}
    mock_impact = {"estimated_downtime_min": 35.0, "production_loss_units": 150}
    mock_peak = {"temperature": 71.0, "vibration": 4.8, "production_rate": 1040.0, "defect_rate": 3.2}
    res = run_recovery_simulation("M03", mock_rca, mock_impact, mock_peak)
    print("\n" + "-"*50)
    print("         RECOVERY SIMULATION RESULTS")
    print("-"*50)
    for opt in res["options"]:
        print(f"Option {opt['option_id']}: {opt['name']}")
        print(f"  Downtime:               {opt['downtime_min']} minutes")
        print(f"  Production Loss:        {opt['production_loss_units']} units")
        print(f"  Risk:                   {opt['risk_level']}")
        print(f"  Operational Loss Score: {opt['operational_loss_score']}")
        print(f"  Maintenance Cost:       ${opt['maintenance_cost_usd']}")
        print(f"  Tradeoff:               {opt['tradeoff']}\n")
