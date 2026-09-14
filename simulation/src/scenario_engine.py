import math
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List

from src.config import MACHINES_CONFIG
from src.models import MachineTelemetry, MaintenanceRecord

# Canonical Scenarios
NORMAL_01_STABLE_PRODUCTION = "NORMAL_01_STABLE_PRODUCTION"
NORMAL_02_HIGH_DEMAND_STABLE = "NORMAL_02_HIGH_DEMAND_STABLE"
NORMAL_03_MINOR_VARIATION = "NORMAL_03_MINOR_VARIATION"

DISRUPTION_01_COOLING_SYSTEM_DEGRADATION = "DISRUPTION_01_COOLING_SYSTEM_DEGRADATION"
DISRUPTION_02_BEARING_DEGRADATION = "DISRUPTION_02_BEARING_DEGRADATION"
DISRUPTION_03_THROUGHPUT_DEGRADATION = "DISRUPTION_03_THROUGHPUT_DEGRADATION"

def resolve_machine_state(t: MachineTelemetry) -> str:
    """Derive the state strictly from the telemetry values, not time."""
    cfg = MACHINES_CONFIG.get(t.machine_id)
    if not cfg:
        return "HEALTHY"
        
    crit = cfg["critical_limits"]
    warn = cfg["safe_limits"]
    
    if t.temperature >= crit["temperature_max"] or t.vibration >= crit["vibration_max"] or t.throughput <= crit["throughput_min"] or t.defect_rate >= crit["defect_rate_max"]:
        return "CRITICAL"
    if t.temperature >= warn["temperature_max"] or t.vibration >= warn["vibration_max"] or t.throughput <= warn["throughput_min"] or t.defect_rate >= warn["defect_rate_max"]:
        return "WARNING"
    return "HEALTHY"

def generate_telemetry(
    machine_id: str,
    step: int,
    rng: np.random.Generator,
    active_scenario: str = NORMAL_01_STABLE_PRODUCTION,
    severity: float = 0.0,
    start_time: datetime = None
) -> MachineTelemetry:
    
    cfg = MACHINES_CONFIG[machine_id]
    base = cfg["baseline"]
    
    if start_time is None:
        start_time = datetime.utcnow()
        
    timestamp = (start_time + timedelta(seconds=step)).isoformat() + "Z"

    # Base noise
    noise_scale = 1.0
    if active_scenario == NORMAL_03_MINOR_VARIATION:
        noise_scale = 2.5

    temp = base["temperature"] + rng.normal(0, 0.4 * noise_scale)
    vib = max(0.1, base["vibration"] + rng.normal(0, 0.05 * noise_scale))
    pres = base["pressure"] + rng.normal(0, 0.5 * noise_scale)
    pwr = base["power_consumption"] + rng.normal(0, 0.3 * noise_scale)
    
    # Base throughput with demand shift
    throughput_base = base["throughput_uph"]
    if active_scenario == NORMAL_02_HIGH_DEMAND_STABLE:
        throughput_base = min(throughput_base * 1.1, throughput_base + 150)
        temp += 2.0  # slightly hotter when running faster
        pwr += 1.5
    
    prod = max(0.0, throughput_base + rng.normal(0, 8.0 * noise_scale))
    defect = max(0.01, base["defect_rate"] + rng.normal(0, 0.03 * noise_scale))

    s = min(1.0, max(0.0, severity))
    
    if active_scenario == DISRUPTION_01_COOLING_SYSTEM_DEGRADATION:
        temp += 29.0 * s
        vib += 2.0 * (s ** 1.3)
        prod -= 360.0 * s
        defect += 1.5 * (s ** 1.2)
        pwr += 5.0 * s
        
    elif active_scenario == DISRUPTION_02_BEARING_DEGRADATION:
        vib += 4.2 * s
        temp += 22.0 * s
        prod -= 400.0 * s
        defect += 2.8 * s
        
    elif active_scenario == DISRUPTION_03_THROUGHPUT_DEGRADATION:
        prod -= 850.0 * s
        temp += 10.0 * s
        vib += 0.8 * s
        # Quality might remain relatively stable
        defect += 0.5 * s

    # Calculate dependent variables
    cycle = base["cycle_time"]
    if prod > 0:
        cycle = base["cycle_time"] * (base["throughput_uph"] / prod)
    
    qual = max(0.0, 100.0 - defect)

    # Mock maintenance history
    m_history = []
    if machine_id == "M03":
        m_history = [
            MaintenanceRecord(date="2026-03-15", type="Preventive", description="Cooling system flushed"),
            MaintenanceRecord(date="2026-06-22", type="Inspection", description="Spindle bearings checked")
        ]

    t = MachineTelemetry(
        machine_id=machine_id,
        machine_name=cfg["name"],
        line_id=cfg["line_id"],
        timestamp=timestamp,
        step=step,
        throughput=round(prod, 1),
        cycle_time=round(cycle, 1),
        temperature=round(temp, 2),
        vibration=round(vib, 3),
        pressure=round(pres, 2),
        power_consumption=round(pwr, 2),
        quality=round(qual, 1),
        defect_rate=round(defect, 3),
        maintenance_history=m_history,
        active_fault=active_scenario if s > 0 else None,
        production_orders=["ORD-7742", "ORD-7743"]
    )
    
    # State is derived strictly from telemetry
    t.state = resolve_machine_state(t)
    return t
