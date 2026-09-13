"""
==============================================================================
               CAUSEN AI: Industrial Decision & Recovery System
==============================================================================
Main End-to-End Simulation Prototype Runner

Flow:
1. Generate / load synthetic multi-machine industrial data
2. Run Isolation Forest anomaly detection
3. Identify affected machine and sensor contributions
4. Perform Explainable Root Cause Analysis (RCA)
5. Predict operational impact (loss, downtime, scrap, downstream delay)
6. Run What-If Recovery Simulations (4 industrial strategies)
7. Execute Multi-Criteria Decision Engine
8. Trigger Simulated Automated Workflow (ticketing, alerting, SCADA rerouting)
9. Generate Visualizations (5 Matplotlib charts + Plotly dashboard)
10. Print CAUSEN AI Executive Terminal Report
==============================================================================
"""

import sys
import argparse
from pathlib import Path

# Configure UTF-8 encoding for Windows console compatibility
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path so modules resolve cleanly
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from src.config import (
    DATA_FILE,
    VISUALIZATIONS_DIR,
    MACHINES_CONFIG,
    FLAGSHIP_MACHINE,
    FLAGSHIP_SCENARIO
)
from src.data_simulation import generate_industrial_data
from src.anomaly_detection import run_anomaly_detection
from src.root_cause_analysis import perform_root_cause_analysis
from src.impact_prediction import predict_operational_impact
from src.recovery_simulation import run_recovery_simulation
from src.decision_engine import make_recovery_decision
from src.workflow_automation import trigger_workflow_automation
from src.visualizations import generate_all_visualizations


def run_pipeline(
    scenario: str = FLAGSHIP_SCENARIO,
    machine_id: str = FLAGSHIP_MACHINE,
    n_steps: int = 120,
    generate_plots: bool = True
) -> dict:
    """Executes the complete CAUSEN AI 10-step intelligence pipeline."""

    print("\n" + "="*60)
    print("      INITIALIZING CAUSEN AI INDUSTRIAL SIMULATOR")
    print("="*60)
    print(f"Target Factory Topology:  10 Connected Production Machines (M01 - M10)")
    print(f"Target Machine:          {machine_id} ({MACHINES_CONFIG[machine_id]['name']})")
    print(f"Active Scenario:         {scenario}")
    print(f"Simulation Steps:        {n_steps} (30s intervals)")

    # 1. Generate industrial telemetry
    print("\n[STEP 1] Generating multi-machine telemetry stream...")
    df = generate_industrial_data(
        n_steps=n_steps,
        anomaly_scenario=scenario,
        affected_machine=machine_id,
        anomaly_start_step=40,
        anomaly_peak_step=85,
        save_csv=True
    )

    # 2 & 3. Detect anomalies and identify affected machine
    print("\n[STEP 2 & 3] Running Isolation Forest Anomaly Detection...")
    df_detected, detection_summary = run_anomaly_detection(df, baseline_steps=40)

    print(f"  • Total Records Analyzed:     {detection_summary['total_records']}")
    print(f"  • Abnormal Records Flagged:   {detection_summary['num_anomalies']} ({detection_summary['anomaly_rate_pct']}%)")
    print(f"  • Primary Affected Machine:   {detection_summary['primary_machine']} - {detection_summary['primary_machine_name']}")
    print("  • Outlier Sensor Deviations at Peak:")
    for sensor in detection_summary["top_contributing_sensors"][:3]:
        print(f"      - {sensor['sensor'].upper()}: observed {sensor['observed']} (baseline {sensor['baseline_mean']}, z-score {sensor['z_score']})")

    # 4. Perform Root Cause Analysis
    print("\n[STEP 4] Executing Explainable Root Cause Analysis (RCA)...")
    rca = perform_root_cause_analysis(detection_summary)
    print(f"  • Probable Cause:  {rca['probable_root_cause']}")
    print(f"  • AI Confidence:   {rca['confidence']}%")
    print(f"  • Severity Level:  {rca['severity']}")
    print(f"  • Reasoning:\n    {rca['reason']}")

    # 5. Predict Operational Impact
    print("\n[STEP 5] Calculating Operational Impact & Loss Score...")
    impact = predict_operational_impact(rca, detection_summary["peak_record"])
    print(f"  • Production Loss:       {impact['production_loss_units']} units")
    print(f"  • Estimated Downtime:    {impact['estimated_downtime_min']} minutes")
    print(f"  • Downstream Delay:      {impact['downstream_delay_min']} minutes")
    print(f"  • Expected Defect Delta: +{impact['expected_defect_increase_pct']}%")
    print(f"  • Operational Loss:      {impact['operational_loss_score']} ({impact['loss_category']})")

    # 6. Run What-If Recovery Simulations
    print("\n[STEP 6] Running What-If Recovery Simulations (4 Strategies)...")
    sim_results = run_recovery_simulation(
        machine_id,
        rca,
        impact,
        detection_summary["peak_record"]
    )
    print("  ------------------------------------------------")
    print("             RECOVERY SIMULATION RESULTS")
    print("  ------------------------------------------------")
    for opt in sim_results["options"]:
        print(f"  Option {opt['option_id']}: {opt['name']}")
        print(f"    Downtime:               {opt['downtime_min']} minutes")
        print(f"    Production Loss:        {opt['production_loss_units']} units")
        print(f"    Risk Level:             {opt['risk_level']}")
        print(f"    Operational Loss Score: {opt['operational_loss_score']}")
        print(f"    Maintenance Cost:       ${opt['maintenance_cost_usd']}\n")

    # 7. Decision Engine Recommendation
    print("[STEP 7] Decision Engine Multi-Criteria Evaluation...")
    decision = make_recovery_decision(
        machine_id,
        rca,
        impact,
        sim_results["options"]
    )
    print(f"  • Recommended Strategy:   {decision['recommended_action']}")
    print(f"  • Engine Confidence:      {decision['confidence']}%")
    print(f"  • Expected Loss Score:    {decision['expected_loss_score']}")

    # 8. Trigger Automated Workflow Simulation
    print("\n[STEP 8] Executing Simulated Workflow Automation...")
    workflow = trigger_workflow_automation(machine_id, rca, decision)
    print("  [WORKFLOW STARTED]")
    for act in workflow["actions_log"]:
        print(f"    ✓ {act['action']}")
    print("  [WORKFLOW COMPLETED]")

    # 9. Generate Visualizations
    viz_paths = {}
    if generate_plots:
        print("\n[STEP 9] Generating Industrial Telemetry & Strategy Visualizations...")
        viz_paths = generate_all_visualizations(
            df=df,
            df_detected=df_detected,
            machine_id=machine_id,
            simulated_options=sim_results["options"],
            recovery_trajectory=sim_results["recovery_trajectory"]
        )
        print(f"  ✓ Temperature Trajectory:     {viz_paths['temperature_trajectory'].name}")
        print(f"  ✓ Vibration Profile:          {viz_paths['vibration_profile'].name}")
        print(f"  ✓ Production Rate Impact:     {viz_paths['production_rate_impact'].name}")
        print(f"  ✓ Anomaly Detection Scatter:  {viz_paths['anomaly_detection_scatter'].name}")
        print(f"  ✓ Strategy Comparison Chart:  {viz_paths['recovery_comparison'].name}")
        print(f"  ✓ Interactive Dashboard:      {viz_paths['interactive_dashboard'].name}")

    # 10. Display Final Executive CAUSEN AI Report
    machine_name = MACHINES_CONFIG[machine_id]["name"]
    print("\n" + "="*50)
    print("               CAUSEN AI")
    print(" Industrial Decision & Recovery System")
    print("="*50)
    print("\nSTATUS: ANOMALY DETECTED\n")
    print(f"Affected Machine:\n{machine_name}\n")
    print(f"Probable Root Cause:\n{rca['probable_root_cause']}\n")
    print(f"Confidence:\n{int(round(rca['confidence']))}%\n")
    print(f"Operational Impact:")
    print(f"Production Loss:    {impact['production_loss_units']} units")
    print(f"Estimated Downtime: {int(impact['estimated_downtime_min'])} minutes")
    print(f"Downstream Delay:   {int(impact['downstream_delay_min'])} minutes\n")
    print(f"WHAT-IF SIMULATION:")
    print(f"{len(sim_results['options'])} recovery strategies evaluated.\n")
    print(f"BEST RECOVERY STRATEGY:")
    print(f"{decision['recommended_action']}\n")
    print(f"Expected Operational Loss Score:")
    print(f"{decision['expected_loss_score']}\n")
    print(f"AUTOMATED ACTIONS:")
    print("✓ Maintenance Ticket Created")
    print("✓ Supervisor Alerted")
    print(f"✓ Workload Redistributed to {decision['target_line']}\n")
    print("="*50)
    print("         RECOVERY PLAN GENERATED")
    print("="*50 + "\n")

    return {
        "detection_summary": detection_summary,
        "rca": rca,
        "impact": impact,
        "sim_results": sim_results,
        "decision": decision,
        "workflow": workflow,
        "visualizations": viz_paths
    }


# Add backend to sys.path to access AI engine
BACKEND_DIR = CURRENT_DIR.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai_engine.orchestrator import run_ai_pipeline
from ai_engine.models import PipelineRequest


def run_manual_pipeline(inputs: dict, generate_plots: bool = True) -> dict:
    """Executes the dynamic simulation pipeline for custom user-entered manual values."""
    m_id = inputs.get("machine", "M03")
    m_name = MACHINES_CONFIG.get(m_id, {}).get("name", f"Machine {m_id}")

    print("\n" + "="*60)
    print("      CAUSEN AI: MANUAL INDUSTRIAL SIMULATION")
    print("="*60)
    print(f"Machine:             {m_id} - {m_name}")
    print(f"Temperature:         {inputs.get('temperature', 48.0)} °C")
    print(f"Vibration:           {inputs.get('vibration', 1.4)} mm/s")
    print(f"Pressure:            {inputs.get('pressure', 101.3)} kPa")
    print(f"Power Consumption:   {inputs.get('power_consumption', 19.5)} kW")
    print(f"Throughput:          {inputs.get('production_rate', 1400.0)} units/hour")
    print(f"Defect Rate:         {inputs.get('defect_rate', 0.8)} %")
    print(f"Machine Status:      {inputs.get('status', 'Normal')}")
    print(f"Maintenance Status:  {inputs.get('maintenance', 'Recently Maintained')}")

    # Map inputs to telemetry dictionary
    telemetry = {
        "temperature": inputs.get("temperature", 48.0),
        "vibration": inputs.get("vibration", 1.4),
        "pressure": inputs.get("pressure", 101.3),
        "power_consumption": inputs.get("power_consumption", 19.5),
        "throughput": inputs.get("production_rate", 1400.0),
        "defect_rate": inputs.get("defect_rate", 0.8)
    }

    # Run Real AI Pipeline
    req = PipelineRequest(machine_id=m_id, telemetry=telemetry)
    res = run_ai_pipeline(req)

    anomaly = res.anomaly
    rca = res.rca
    impact = res.impact
    options = res.recovery_simulations
    decision = res.decision

    print("\n[STEP 3] Dynamic Anomaly Detection...")
    print(f"  • Composite Anomaly Score:  {anomaly.anomaly_score} / 100")
    print(f"  • Status Category:          {anomaly.severity}")
    print("  • Detected Issues:")
    for sig in anomaly.signals:
        if sig.is_anomalous if hasattr(sig, 'is_anomalous') else sig.deviation_percent > 10:
            print(f"      - {sig.name.upper()}: {sig.current} (Dev {sig.deviation_percent}%)")

    print("\n[STEP 4] Explainable Root Cause Analysis (RCA)...")
    print(f"  • Primary Cause:            {rca.probable_cause.name}")
    print(f"  • Confidence:               {round(rca.probable_cause.confidence * 100, 1)}%")
    sec_cause = rca.alternatives[0].name if rca.alternatives else "None"
    print(f"  • Secondary Possibility:    {sec_cause}")
    print(f"  • Dynamic AI Explanation:\n    \"{rca.summary}\"")
    print(f"  • Recommended Focus:        {rca.probable_cause.name}")

    print("\n[STEP 5] Operational Impact Prediction...")
    downtime_min = impact.impact.downtime.projected_minutes or impact.impact.downtime.observed_minutes
    print(f"  • Estimated Downtime:       {int(downtime_min)} minutes")
    print(f"  • Production Loss:          {round(impact.impact.production.loss_rate * 100, 1) if impact.impact.production.loss_rate else 0}%")
    print(f"  • Defect Risk Level:        {impact.impact.quality.impact}")
    print(f"  • Downstream Delay:         0 minutes")
    print(f"  • Operational Impact Level: {impact.confidence} (Score: {impact.impact.financial.estimated_loss or 0})")

    print("\n[STEP 6] What-If Recovery Simulations (4 Options)...")
    print("  ------------------------------------------------")
    print("             RECOVERY SIMULATION RESULTS")
    print("  ------------------------------------------------")
    for opt in options:
        print(f"  Option {opt.action.action_id}: {opt.action.name}")
        print(f"    Downtime Risk:          {round(opt.after.downtime_risk * 100, 1)}%")
        print(f"    Production Loss Rate:   {round(opt.after.production_loss_rate * 100, 1) if opt.after.production_loss_rate else 0}%")
        print(f"    Defect Risk:            {opt.after.anomaly_severity}")
        print(f"    Operational Loss Score: {opt.delta.anomaly_score_change}")
        print(f"    Effectiveness:          {round(opt.recovery_effectiveness * 100, 1)}%\n")

    print("[STEP 7] Decision Engine Evaluation...")
    print(f"  • Recommended Strategy:     {decision.decision.recommended_action}")
    print(f"  • Engine Confidence:        {round(decision.decision.decision_confidence * 100, 1)}%")
    top_score = decision.ranked_options[0].score if decision.ranked_options else 0
    print(f"  • Expected Loss Score:      {top_score}")

    print("\n[STEP 10] Automated Recovery Workflow Simulation...")
    print("  [WORKFLOW STARTED]")
    print("    ✓ [1/5] Anomaly detected and logged")
    print(f"    ✓ [2/5] Root cause identified: {rca.probable_cause.name}")
    print("    ✓ [3/5] Maintenance ticket created (#INC-2049)")
    print("    ✓ [4/5] Production supervisor notified via SCADA push")
    print(f"    ✓ [5/5] Recovery strategy activated: {decision.decision.recommended_action}")
    print("  [WORKFLOW COMPLETED]")

    # Executive Output Banner
    print("\n" + "="*50)
    print("               CAUSEN AI")
    print(" Industrial Decision & Recovery System")
    print("="*50)
    print(f"\nSTATUS: {anomaly.severity}\n")
    print(f"Affected Machine:\n{m_id} - {m_name}\n")
    print(f"Probable Root Cause:\n{rca.probable_cause.name}\n")
    print(f"Confidence:\n{int(round(rca.probable_cause.confidence * 100))}%\n")
    print("Operational Impact:")
    print(f"Production Loss Rate: {round(impact.impact.production.loss_rate * 100, 1) if impact.impact.production.loss_rate else 0}%")
    print(f"Estimated Downtime:   {int(downtime_min)} minutes")
    print(f"Downstream Delay:     0 minutes\n")
    print("WHAT-IF SIMULATION:")
    print(f"{len(options)} recovery strategies evaluated.\n")
    print("BEST RECOVERY STRATEGY:")
    print(f"{decision.decision.recommended_action}\n")
    print("Expected Operational Loss Score:")
    print(f"{top_score}\n")
    print("AUTOMATED ACTIONS:")
    print("✓ Maintenance Ticket Created")
    print("✓ Supervisor Alerted")
    print(f"✓ Recovery Strategy Activated ({decision.decision.recommended_action})\n")
    print("="*50)
    print("         RECOVERY PLAN GENERATED")
    print("="*50 + "\n")

    return res.model_dump()


def interactive_cli():
    """Interactive prompt allowing user to manually type in sensor values."""
    print("\n" + "="*60)
    print("   CAUSEN AI: INTERACTIVE MANUAL SIMULATION MODE")
    print("="*60)
    print("Enter custom values below (or press Enter to accept defaults):\n")

    try:
        machine = input("Machine ID [M01, M02, M03, M04] (default M03): ").strip().upper() or "M03"
        temp = float(input("Temperature in °C [Normal 30-65] (default 48.0): ").strip() or "48.0")
        vib = float(input("Vibration in mm/s [Normal 0.5-3.0] (default 1.4): ").strip() or "1.4")
        pres = float(input("Pressure in kPa [Normal 95-105] (default 101.3): ").strip() or "101.3")
        power = float(input("Power Consumption in kW [Normal 15-25] (default 19.5): ").strip() or "19.5")
        prod = float(input("Production Throughput in u/h [Nominal 1400] (default 1400): ").strip() or "1400")
        defect = float(input("Defect Rate % [Normal < 1.0%] (default 0.8): ").strip() or "0.8")
    except ValueError:
        print("Invalid numerical input. Using defaults.")
        temp, vib, pres, power, prod, defect = 48.0, 1.4, 101.3, 19.5, 1400.0, 0.8
        machine = "M03"

    inputs = {
        "machine": machine,
        "temperature": temp,
        "vibration": vib,
        "pressure": pres,
        "power_consumption": power,
        "production_rate": prod,
        "defect_rate": defect,
        "status": "Warning" if (temp > 65 or vib > 3.0 or defect > 3.0) else "Normal",
        "maintenance": "Maintenance Due" if (temp > 70 or vib > 4.0) else "Recently Maintained"
    }

    run_manual_pipeline(inputs)


def main():
    parser = argparse.ArgumentParser(description="CAUSEN AI: Industrial Decision & Recovery System Prototype")
    parser.add_argument(
        "--scenario",
        type=str,
        default=FLAGSHIP_SCENARIO,
        choices=[
            "cooling_system_degradation",
            "bearing_wear",
            "motor_overheat",
            "mechanical_misalignment",
            "material_defect",
            "critical_breakdown"
        ],
        help="Industrial fault scenario to simulate"
    )
    parser.add_argument(
        "--machine",
        type=str,
        default=FLAGSHIP_MACHINE,
        help="Target machine ID (M01 to M10)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=120,
        help="Number of time steps to simulate (default: 120)"
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="Skip chart rendering"
    )
    # Manual Input arguments
    parser.add_argument("--manual", action="store_true", help="Run with manual sensor inputs")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive terminal prompt to enter sensor values")
    parser.add_argument("--temp", type=float, default=None, help="Manual Temperature (°C)")
    parser.add_argument("--vib", type=float, default=None, help="Manual Vibration (mm/s)")
    parser.add_argument("--pres", type=float, default=None, help="Manual Pressure (kPa)")
    parser.add_argument("--power", type=float, default=None, help="Manual Power Consumption (kW)")
    parser.add_argument("--prod", type=float, default=None, help="Manual Production Throughput (u/h)")
    parser.add_argument("--defect", type=float, default=None, help="Manual Defect Rate (%%)")

    args = parser.parse_args()

    if args.interactive:
        interactive_cli()
    elif args.manual or (args.temp is not None or args.vib is not None):
        inputs = {
            "machine": args.machine or "M03",
            "temperature": args.temp if args.temp is not None else 48.0,
            "vibration": args.vib if args.vib is not None else 1.4,
            "pressure": args.pres if args.pres is not None else 101.3,
            "power_consumption": args.power if args.power is not None else 19.5,
            "production_rate": args.prod if args.prod is not None else 1400.0,
            "defect_rate": args.defect if args.defect is not None else 0.8,
            "status": "Warning" if ((args.temp or 0) > 65 or (args.vib or 0) > 3.0) else "Normal"
        }
        run_manual_pipeline(inputs, generate_plots=not args.no_viz)
    else:
        run_pipeline(
            scenario=args.scenario,
            machine_id=args.machine,
            n_steps=args.steps,
            generate_plots=not args.no_viz
        )


if __name__ == "__main__":
    main()

