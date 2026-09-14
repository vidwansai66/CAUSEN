"""
CAUSEN AI: Configuration and Factory Topology
Defines the 10 industrial machines, baseline operational parameters,
downstream topologies, and fault profiles.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VISUALIZATIONS_DIR = BASE_DIR / "visualizations"
DATA_FILE = DATA_DIR / "industrial_data.csv"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)

# 10 Industrial Machines Configuration
# Modeled after connected multi-stage automotive/electronics manufacturing plant
MACHINES_CONFIG = {
    "M01": {
        "name": "Machine A - Cutting / Raw Material Feed",
        "role": "Raw Material Feed",
        "line_id": "LINE-1",
        "baseline": {
            "temperature": 42.0,      # °C
            "vibration": 1.2,        # mm/s
            "pressure": 101.3,       # kPa
            "power_consumption": 18.5, # kW
            "cycle_time": 45.0,      # seconds
            "throughput_uph": 1200,  # units/hour (production rate)
            "quality_pct": 99.8,     # %
            "defect_rate": 0.2       # %
        },
        "downstream": ["M02"]
    },
    "M02": {
        "name": "Machine B1 - Assembly Line 1",
        "role": "Assembly Line 1",
        "line_id": "LINE-1",
        "baseline": {
            "temperature": 45.0,
            "vibration": 1.5,
            "pressure": 103.0,
            "power_consumption": 22.0,
            "cycle_time": 46.0,
            "throughput_uph": 1180,
            "quality_pct": 99.5,
            "defect_rate": 0.5
        },
        "downstream": ["M03"]
    },
    "M03": {
        "name": "Machine B2 - Assembly Line 2",
        "role": "Assembly Line 2 (Primary Demo)",
        "line_id": "LINE-2",
        "baseline": {
            "temperature": 42.0,
            "vibration": 1.2,
            "pressure": 100.5,
            "power_consumption": 19.5,
            "cycle_time": 45.0,
            "throughput_uph": 1400,
            "quality_pct": 99.7,
            "defect_rate": 0.3
        },
        "downstream": ["M04"]
    },
    "M04": {
        "name": "Machine C - Quality Inspection",
        "role": "Quality Inspection",
        "line_id": "LINE-2",
        "baseline": {
            "temperature": 40.0,
            "vibration": 1.0,
            "pressure": 98.0,
            "power_consumption": 14.0,
            "cycle_time": 43.0,
            "throughput_uph": 1380,
            "quality_pct": 99.8,
            "defect_rate": 0.2
        },
        "downstream": ["M05"]
    },
    "M05": {
        "name": "Machine D - Packaging Unit",
        "role": "Packaging Unit",
        "line_id": "LINE-2",
        "baseline": {
            "temperature": 38.0,
            "vibration": 0.9,
            "pressure": 95.0,
            "power_consumption": 12.5,
            "cycle_time": 40.0,
            "throughput_uph": 1350,
            "quality_pct": 99.7,
            "defect_rate": 0.3
        },
        "downstream": ["M06"]
    },
    "M06": {
        "name": "Machine E - Material Transfer",
        "role": "Material Transfer",
        "line_id": "LINE-2",
        "baseline": {
            "temperature": 39.0,
            "vibration": 1.1,
            "pressure": 99.0,
            "power_consumption": 15.0,
            "cycle_time": 41.0,
            "throughput_uph": 1350,
            "quality_pct": 99.7,
            "defect_rate": 0.3
        },
        "downstream": ["M07"]
    },
    "M07": {
        "name": "Machine F - Secondary Assembly (Backup / Reroute Line)",
        "role": "Secondary Assembly",
        "line_id": "LINE-3",
        "baseline": {
            "temperature": 44.0,
            "vibration": 1.4,
            "pressure": 102.0,
            "power_consumption": 21.0,
            "cycle_time": 47.0,
            "throughput_uph": 1320,
            "quality_pct": 99.4,
            "defect_rate": 0.6
        },
        "downstream": ["M08"]
    },
    "M08": {
        "name": "Machine G - Finishing Station",
        "role": "Finishing Station",
        "line_id": "LINE-3",
        "baseline": {
            "temperature": 41.0,
            "vibration": 1.0,
            "pressure": 97.5,
            "power_consumption": 16.0,
            "cycle_time": 44.0,
            "throughput_uph": 1300,
            "quality_pct": 99.6,
            "defect_rate": 0.4
        },
        "downstream": ["M09"]
    },
    "M09": {
        "name": "Machine H - Final Inspection",
        "role": "Final Inspection",
        "line_id": "LINE-3",
        "baseline": {
            "temperature": 40.0,
            "vibration": 0.8,
            "pressure": 96.0,
            "power_consumption": 13.0,
            "cycle_time": 42.0,
            "throughput_uph": 1280,
            "quality_pct": 99.8,
            "defect_rate": 0.2
        },
        "downstream": ["M10"]
    },
    "M10": {
        "name": "Machine I - Dispatch / Palletizing",
        "role": "Dispatch / Palletizing",
        "line_id": "LINE-3",
        "baseline": {
            "temperature": 37.0,
            "vibration": 0.7,
            "pressure": 94.0,
            "power_consumption": 11.0,
            "cycle_time": 39.0,
            "throughput_uph": 1250,
            "quality_pct": 99.7,
            "defect_rate": 0.3
        },
        "downstream": []
    }
}

# Sensor feature names used for ML and analysis
FEATURE_COLUMNS = [
    "temperature",
    "vibration",
    "pressure",
    "power_consumption",
    "production_rate",
    "defect_rate"
]

# Primary demo settings
FLAGSHIP_MACHINE = "M03"
FLAGSHIP_SCENARIO = "cooling_system_degradation"
REROUTE_TARGET_MACHINE = "M07"
REROUTE_TARGET_LINE = "LINE-3"

# Calculate and inject dynamic thresholds based on canonical simulator math
for m_id, cfg in MACHINES_CONFIG.items():
    base = cfg["baseline"]
    cfg["safe_limits"] = {
        "temperature_max": round(base["temperature"] + 15.0, 1),
        "vibration_max": round(base["vibration"] + 1.2, 2),
        "throughput_min": round(base["throughput_uph"] * 0.85, 1),
        "defect_rate_max": round(base["defect_rate"] + 0.5, 2)
    }
    cfg["critical_limits"] = {
        "temperature_max": round(base["temperature"] + 30.0, 1),
        "vibration_max": round(base["vibration"] + 3.0, 2),
        "throughput_min": round(base["throughput_uph"] * 0.5, 1),
        "defect_rate_max": round(base["defect_rate"] + 4.0, 2)
    }
