"""
CAUSEN AI: Root Cause Analysis (RCA) Engine
Explainable hybrid rule-based + AI logic system that correlates multi-sensor
deviations against industrial failure mode matrices to identify root causes with confidence scores.
"""

from typing import Dict, Any, List


class RootCauseAnalyzer:
    """
    Industrial Root Cause Analysis engine diagnosing machine failure signatures.
    """

    def __init__(self):
        pass

    def diagnose(
        self,
        machine_id: str,
        peak_record: Dict[str, Any],
        contributing_sensors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate sensor deviations and map to failure mode knowledge base.
        """
        temp = peak_record.get("temperature", 42.0)
        vib = peak_record.get("vibration", 1.2)
        pres = peak_record.get("pressure", 100.0)
        pwr = peak_record.get("power_consumption", 19.5)
        prod = peak_record.get("production_rate", 1400.0)
        defect = peak_record.get("defect_rate", 0.3)
        machine_name = peak_record.get("machine_name", f"Machine {machine_id}")

        contributing_names = {item["sensor"] for item in contributing_sensors}
        top_sensor = contributing_sensors[0]["sensor"] if contributing_sensors else ""

        # Failure mode evaluation matrix
        hypotheses = []

        # 1. Bearing Wear / Mechanical Friction
        # Vibration is elevated; if vibration is the primary deviating channel, this is the leading hypothesis
        if vib >= 2.5 or top_sensor == "vibration":
            base_conf = 88.0 if top_sensor == "vibration" else 75.0
            confidence = min(97.0, base_conf + (vib - 2.5) * 5.0 + max(0, (temp - 45.0) * 0.4))
            hypotheses.append({
                "cause": "Bearing Wear & Mechanical Friction",
                "confidence": round(confidence, 1),
                "severity": "CRITICAL" if vib >= 4.0 else "HIGH",
                "reason": (
                    f"High vibration ({vib} mm/s) combined with an abnormal increase in operational "
                    f"temperature ({temp}°C) matches the historical failure pattern of bearing "
                    f"raceway degradation and loss of lubrication."
                ),
                "evidence": [
                    f"Vibration reached {vib} mm/s (normal baseline limit < 1.8 mm/s)",
                    f"Frictional heating detected with temperature at {temp}°C",
                    f"Degradation rate indicates imminent spindle bearing seizure"
                ],
                "recommended_focus": "Check bearing lubrication grease, inspect race surfaces, and measure shaft eccentricity."
            })

        # 2. Cooling System Degradation / Thermal Runaway
        # High temperature (> 60°C); dominant if temperature is the primary deviating channel
        if temp >= 60.0 and ("temperature" in contributing_names):
            base_conf = 88.0 if top_sensor == "temperature" else 76.0
            confidence = min(96.0, base_conf + (temp - 60.0) * 1.5 + (vib - 1.2) * 1.5)
            hypotheses.append({
                "cause": "Cooling System Degradation & Thermal Stress",
                "confidence": round(confidence, 1),
                "severity": "CRITICAL" if temp >= 68.0 else "HIGH",
                "reason": (
                    f"Progressive temperature rise to {temp}°C (baseline ~42°C) combined with thermal "
                    f"expansion vibration of {vib} mm/s indicates severe heat exchange failure "
                    f"in the primary cooling loop."
                ),
                "evidence": [
                    f"Temperature elevated by +{round(temp - 42.0, 1)}°C above normal limit",
                    f"Vibration elevated to {vib} mm/s due to thermal tolerance degradation",
                    f"Throughput degraded by {round(1400.0 - prod, 0)} units/hr due to thermal throttling"
                ],
                "recommended_focus": "Inspect coolant pump pressure, radiator clogging, and heat exchange sensors."
            })

        # 3. Motor Overheating / Electrical Drive Fault
        # Extreme temperature + abnormal power consumption spike
        if pwr >= 28.0 or (temp >= 65.0 and pwr >= 24.0):
            confidence = min(95.0, 75.0 + (pwr - 22.0) * 1.5 + (temp - 50.0) * 0.7)
            hypotheses.append({
                "cause": "Motor Stator Overheating & Electrical Drive Stress",
                "confidence": round(confidence, 1),
                "severity": "CRITICAL",
                "reason": (
                    f"Abnormal power consumption draw ({pwr} kW vs baseline ~20 kW) with elevated "
                    f"stator temperature ({temp}°C) signifies electrical winding overload and insulation stress."
                ),
                "evidence": [
                    f"Power consumption spiked to {pwr} kW (+{round(pwr - 20.0, 1)} kW above nominal)",
                    f"Operating temperature at {temp}°C indicates thermal dissipation saturation"
                ],
                "recommended_focus": "Check VFD drive inverter parameters, stator coil resistance, and cooling fan."
            })

        # 4. Mechanical Misalignment
        # Low production rate with elevated vibration but normal temperature
        if prod < 1000.0 and vib >= 2.5 and temp < 55.0:
            confidence = min(91.0, 70.0 + (1000.0 - prod) * 0.04 + (vib - 2.0) * 5.0)
            hypotheses.append({
                "cause": "Mechanical Shaft / Coupler Misalignment",
                "confidence": round(confidence, 1),
                "severity": "MEDIUM",
                "reason": (
                    f"Significant production throughput depression ({prod} units/h) paired with elevated "
                    f"radial vibration ({vib} mm/s) under normal thermal conditions indicates angular or "
                    f"parallel shaft misalignment."
                ),
                "evidence": [
                    f"Production dropped to {prod} units/h",
                    f"Vibration elevated to {vib} mm/s without proportional thermal runaway"
                ],
                "recommended_focus": "Perform laser alignment on drive couplings and inspect mount bolts."
            })

        # 5. Raw Material Quality Issue
        # High defect rate with normal mechanical sensors
        if defect >= 2.5 and temp < 48.0 and vib < 1.8:
            confidence = min(93.0, 75.0 + defect * 2.5)
            hypotheses.append({
                "cause": "Raw Material Stock Defect / Feed Quality Variation",
                "confidence": round(confidence, 1),
                "severity": "MEDIUM",
                "reason": (
                    f"Surge in scrap defect rate to {defect}% while mechanical sensors (temp {temp}°C, "
                    f"vib {vib} mm/s) operate within normal baseline tolerances points directly to incoming "
                    f"raw material metallurgical or dimensional defect."
                ),
                "evidence": [
                    f"Defect rate spiked to {defect}% (normal threshold < 0.5%)",
                    f"Mechanical and electrical health indicators remain stable and healthy"
                ],
                "recommended_focus": "Quarantine incoming material batch lot and alert upstream vendor quality team."
            })

        # Fallback if no specific rule matched
        if not hypotheses:
            hypotheses.append({
                "cause": "Unspecified Sensor Correlation Anomaly",
                "confidence": 65.0,
                "severity": "WARNING",
                "reason": f"Multivariate outlier detected on {machine_name} with sensor deviations: {[s['sensor'] for s in contributing_sensors]}.",
                "evidence": [f"{s['sensor']}: observed {s['observed']} vs baseline {s['baseline_mean']}" for s in contributing_sensors],
                "recommended_focus": "Perform physical sensor calibration and diagnostic cycle."
            })

        # Select hypothesis with highest confidence
        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        best = hypotheses[0]

        return {
            "machine_id": machine_id,
            "machine_name": machine_name,
            "status": "ANOMALY DETECTED",
            "probable_root_cause": best["cause"],
            "confidence": best["confidence"],
            "severity": best["severity"],
            "reason": best["reason"],
            "evidence": best["evidence"],
            "recommended_focus": best["recommended_focus"],
            "alternative_causes": hypotheses[1:] if len(hypotheses) > 1 else []
        }


def perform_root_cause_analysis(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper from anomaly summary."""
    analyzer = RootCauseAnalyzer()
    machine_id = summary.get("primary_machine", "M03")
    peak_record = summary.get("peak_record", {})
    contributing = summary.get("top_contributing_sensors", [])
    return analyzer.diagnose(machine_id, peak_record, contributing)


if __name__ == "__main__":
    from src.data_simulation import generate_industrial_data
    from src.anomaly_detection import run_anomaly_detection
    df = generate_industrial_data(n_steps=120)
    _, summary = run_anomaly_detection(df)
    rca = perform_root_cause_analysis(summary)
    print("\n" + "="*50)
    print("           ROOT CAUSE ANALYSIS")
    print("="*50)
    print(f"Machine:        {rca['machine_name']} ({rca['machine_id']})")
    print(f"Status:         {rca['status']}")
    print(f"Probable Cause: {rca['probable_root_cause']}")
    print(f"Confidence:     {rca['confidence']}%")
    print(f"Severity:       {rca['severity']}")
    print(f"\nReason:\n{rca['reason']}")
    print("\nEvidence:")
    for ev in rca["evidence"]:
        print(f"  ✓ {ev}")
    print(f"\nRecommended Action: {rca['recommended_focus']}")
