"""
CAUSEN AI: Industrial Telemetry Data Simulation
Generates synthetic, physically plausible telemetry across 10 interconnected machines.
Supports realistic noise, downstream buffer propagation, and progressive fault injection.
"""

import math
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.config import (
    MACHINES_CONFIG,
    FEATURE_COLUMNS,
    DATA_FILE,
    FLAGSHIP_MACHINE,
    FLAGSHIP_SCENARIO
)


def generate_baseline_reading(machine_id: str, step: int, rng: np.random.Generator) -> dict:
    """Generate a single normal baseline reading with slight stochastic fluctuation."""
    cfg = MACHINES_CONFIG[machine_id]
    base = cfg["baseline"]

    # Micro-fluctuations around baseline to simulate living factory environment
    temp_noise = rng.normal(0, 0.4)
    vib_noise = rng.normal(0, 0.05)
    pres_noise = rng.normal(0, 0.5)
    pwr_noise = rng.normal(0, 0.3)
    prod_noise = rng.normal(0, 8.0)
    defect_noise = rng.normal(0, 0.03)

    return {
        "machine_id": machine_id,
        "machine_name": cfg["name"],
        "line_id": cfg["line_id"],
        "temperature": round(float(base["temperature"] + temp_noise), 2),
        "vibration": round(max(0.1, float(base["vibration"] + vib_noise)), 3),
        "pressure": round(float(base["pressure"] + pres_noise), 2),
        "power_consumption": round(float(base["power_consumption"] + pwr_noise), 2),
        "production_rate": round(max(0, float(base["throughput_uph"] + prod_noise)), 1),
        "defect_rate": round(max(0.01, float(base["defect_rate"] + defect_noise)), 3),
        "machine_status": "HEALTHY",
        "maintenance_status": "OK",
        "downstream_delay": 0.0
    }


def inject_fault(
    reading: dict,
    scenario: str,
    severity_fraction: float,
    is_downstream: bool = False,
    upstream_delay: float = 0.0
) -> dict:
    """
    Inject fault dynamics based on scenario and progressive severity fraction (0.0 to 1.0).
    """
    if is_downstream:
        # Downstream machines experience starved throughput and delay propagation
        delay = max(0.0, upstream_delay)
        reading["downstream_delay"] = round(delay, 1)
        if delay > 5.0:
            reading["production_rate"] = round(max(50.0, reading["production_rate"] * (1.0 - 0.4 * severity_fraction)), 1)
            reading["machine_status"] = "WARNING" if delay < 20 else "CRITICAL"
        return reading

    s = min(1.0, max(0.0, severity_fraction))

    if scenario == "cooling_system_degradation" or scenario == "flagship":
        # Target trajectory from Engineer Handoff:
        # Normal: 42°C, 1.2 mm/s, 1400 u/h, 99.7% qual (0.3% defect)
        # Critical: 71°C, 4.8 mm/s, 1040 u/h, 96.8% qual (3.2% defect)
        delta_temp = 29.0 * s
        delta_vib = 3.6 * (s ** 1.3)
        delta_power = 6.5 * s
        delta_prod = -360.0 * s
        delta_defect = 2.9 * (s ** 1.2)

        reading["temperature"] = round(reading["temperature"] + delta_temp, 2)
        reading["vibration"] = round(reading["vibration"] + delta_vib, 3)
        reading["power_consumption"] = round(reading["power_consumption"] + delta_power, 2)
        reading["production_rate"] = round(max(0.0, reading["production_rate"] + delta_prod), 1)
        reading["defect_rate"] = round(min(100.0, reading["defect_rate"] + delta_defect), 3)

    elif scenario == "bearing_wear":
        # High vibration + increasing temp
        reading["vibration"] = round(reading["vibration"] + 3.8 * s, 3)
        reading["temperature"] = round(reading["temperature"] + 22.0 * s, 2)
        reading["production_rate"] = round(max(0.0, reading["production_rate"] - 250.0 * s), 1)
        reading["defect_rate"] = round(reading["defect_rate"] + 1.8 * s, 3)

    elif scenario == "motor_overheat":
        # High temp + abnormal power consumption spike
        reading["temperature"] = round(reading["temperature"] + 32.0 * s, 2)
        reading["power_consumption"] = round(reading["power_consumption"] + 16.0 * s, 2)
        reading["vibration"] = round(reading["vibration"] + 1.2 * s, 3)
        reading["production_rate"] = round(max(0.0, reading["production_rate"] - 200.0 * s), 1)

    elif scenario == "mechanical_misalignment":
        # Low production rate + high vibration
        reading["production_rate"] = round(max(100.0, reading["production_rate"] - 550.0 * s), 1)
        reading["vibration"] = round(reading["vibration"] + 3.2 * s, 3)
        reading["defect_rate"] = round(reading["defect_rate"] + 2.2 * s, 3)

    elif scenario == "material_defect":
        # Defect rate jumps, machine mechanical sensors normal
        reading["defect_rate"] = round(reading["defect_rate"] + 6.5 * s, 3)
        reading["production_rate"] = round(max(0.0, reading["production_rate"] - 150.0 * s), 1)

    elif scenario == "critical_breakdown":
        reading["production_rate"] = round(max(0.0, reading["production_rate"] * (1.0 - s)), 1)
        reading["temperature"] = round(reading["temperature"] + 35.0 * s, 2)
        reading["vibration"] = round(reading["vibration"] + 4.5 * s, 3)
        reading["defect_rate"] = round(reading["defect_rate"] + 5.0 * s, 3)

    # Assign machine status based on degradation severity
    if s < 0.20:
        reading["machine_status"] = "HEALTHY"
    elif s < 0.55:
        reading["machine_status"] = "WARNING"
    else:
        reading["machine_status"] = "CRITICAL"

    return reading


def generate_industrial_data(
    n_steps: int = 120,
    time_step_seconds: int = 30,
    anomaly_scenario: str = FLAGSHIP_SCENARIO,
    affected_machine: str = FLAGSHIP_MACHINE,
    anomaly_start_step: int = 40,
    anomaly_peak_step: int = 85,
    save_csv: bool = True,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic industrial telemetry across all 10 machines.
    
    Includes:
    - Baseline normal behavior (steps 0 to anomaly_start_step)
    - Progressive fault development (anomaly_start_step to anomaly_peak_step)
    - Propagation to downstream machines in the topology
    """
    rng = np.random.default_rng(random_seed)
    start_time = datetime(2026, 9, 10, 10, 0, 0)
    
    rows = []
    machine_ids = list(MACHINES_CONFIG.keys())

    # Find downstream chain for the affected machine
    def get_downstream_chain(m_id):
        chain = []
        curr = m_id
        while curr and MACHINES_CONFIG[curr]["downstream"]:
            nxt = MACHINES_CONFIG[curr]["downstream"][0]
            chain.append(nxt)
            curr = nxt
        return chain

    downstream_machines = get_downstream_chain(affected_machine)

    for step in range(n_steps):
        timestamp = start_time + timedelta(seconds=step * time_step_seconds)
        iso_time = timestamp.isoformat() + "Z"

        # Calculate anomaly severity at this step
        if step < anomaly_start_step:
            severity = 0.0
        elif step <= anomaly_peak_step:
            # S-curve ramp up from 0 to 1.0
            progress = (step - anomaly_start_step) / max(1, (anomaly_peak_step - anomaly_start_step))
            severity = 0.5 * (1 - math.cos(progress * math.pi))
        else:
            # Holds at severe/critical
            severity = 1.0

        # Downstream delay accumulates as throughput drops
        if severity > 0.3:
            # Buffer capacity ~10 mins; delay accumulates progressively
            accumulated_delay = min(35.0, (severity - 0.3) * 35.0)
        else:
            accumulated_delay = 0.0

        for m_id in machine_ids:
            reading = generate_baseline_reading(m_id, step, rng)
            reading["step"] = step
            reading["timestamp"] = iso_time

            if m_id == affected_machine:
                reading = inject_fault(reading, anomaly_scenario, severity, is_downstream=False)
            elif m_id in downstream_machines and accumulated_delay > 0:
                # Downstream stations experience staggered propagation delay
                hop = downstream_machines.index(m_id) + 1
                machine_delay = max(0.0, accumulated_delay - (hop * 1.5))
                reading = inject_fault(
                    reading,
                    anomaly_scenario,
                    severity * (0.85 ** hop),
                    is_downstream=True,
                    upstream_delay=machine_delay
                )

            rows.append(reading)

    df = pd.DataFrame(rows)

    if save_csv:
        df.to_csv(DATA_FILE, index=False)
        print(f"[DATA SIMULATION] Dataset saved successfully to: {DATA_FILE}")
        print(f"[DATA SIMULATION] Total records generated: {len(df)} across {len(machine_ids)} machines.")

    return df


if __name__ == "__main__":
    df = generate_industrial_data(n_steps=120, anomaly_scenario=FLAGSHIP_SCENARIO)
    print(df.head(5))
