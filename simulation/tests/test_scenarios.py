import pytest
import numpy as np
from datetime import datetime, timezone

from src.config import MACHINES_CONFIG
from src.scenario_engine import (
    generate_telemetry,
    resolve_machine_state,
    NORMAL_01_STABLE_PRODUCTION,
    DISRUPTION_01_COOLING_SYSTEM_DEGRADATION,
    DISRUPTION_02_BEARING_DEGRADATION,
    DISRUPTION_03_THROUGHPUT_DEGRADATION
)

def test_normal_telemetry():
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 0, rng, active_scenario=NORMAL_01_STABLE_PRODUCTION, severity=0.0)
    assert t.state == "HEALTHY"
    # Should be close to baseline
    assert 40.0 <= t.temperature <= 44.0
    assert 1380 <= t.throughput <= 1420

def test_cooling_system_degradation():
    rng = np.random.default_rng(42)
    # severity 1.0
    t = generate_telemetry("M03", 20, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    
    # Temperature should be significantly elevated (base 42 + 29 = 71, plus noise)
    assert t.temperature > 65.0
    assert t.throughput < 1200.0
    
    assert resolve_machine_state(t) in ["WARNING", "CRITICAL"]

def test_bearing_degradation():
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=DISRUPTION_02_BEARING_DEGRADATION, severity=1.0)
    
    # Vibration should be significantly elevated (base 1.2 + 4.2 = 5.4, plus noise)
    assert t.vibration > 4.0
    assert t.temperature > 50.0
    
    assert resolve_machine_state(t) in ["WARNING", "CRITICAL"]

def test_throughput_degradation():
    rng = np.random.default_rng(42)
    t = generate_telemetry("M03", 20, rng, active_scenario=DISRUPTION_03_THROUGHPUT_DEGRADATION, severity=1.0)
    
    # Throughput should drop significantly (base 1400 - 850 = 550, plus noise)
    assert t.throughput < 600.0
    assert t.cycle_time > 80.0
    
    assert resolve_machine_state(t) in ["WARNING", "CRITICAL"]

def test_severity_progression():
    rng = np.random.default_rng(42)
    
    t0 = generate_telemetry("M03", 0, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.0)
    t1 = generate_telemetry("M03", 10, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=0.5)
    t2 = generate_telemetry("M03", 20, rng, active_scenario=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity=1.0)
    
    assert t0.temperature < t1.temperature < t2.temperature
    assert t0.throughput > t1.throughput > t2.throughput
    
    assert t0.state == "HEALTHY"
    # State should logically correspond to telemetry thresholds
    assert t1.state in ["HEALTHY", "WARNING"]
    assert t2.state in ["WARNING", "CRITICAL"]

def test_deterministic_seed():
    rng1 = np.random.default_rng(42)
    start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t1 = generate_telemetry("M03", 5, rng1, active_scenario=NORMAL_01_STABLE_PRODUCTION, severity=0.0, start_time=start)

    rng2 = np.random.default_rng(42)
    t2 = generate_telemetry("M03", 5, rng2, active_scenario=NORMAL_01_STABLE_PRODUCTION, severity=0.0, start_time=start)

    assert t1.model_dump() == t2.model_dump()
