"""
CAUSEN AI: Visualization Engine
Generates publication-quality charts and an interactive Plotly dashboard:
1. Temperature over time (with threshold band and recovery)
2. Vibration over time (with ISO mechanical tolerance bands)
3. Production rate before and after anomaly remediation
4. Anomaly detection scatter & decision score timeline
5. Comparison chart of the 4 recovery strategies
"""

from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import VISUALIZATIONS_DIR, MACHINES_CONFIG

# Set clean matplotlib styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "Arial"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def plot_temperature_trajectory(
    df: pd.DataFrame,
    machine_id: str,
    recovery_trajectory: List[Dict[str, Any]],
    output_path: Path = VISUALIZATIONS_DIR / "1_temperature_trajectory.png"
) -> Path:
    """1. Temperature over time with baseline band, anomaly escalation, and recovery."""
    m_df = df[df["machine_id"] == machine_id].copy().sort_values("step")
    steps = m_df["step"].values
    temps = m_df["temperature"].values

    base_temp = MACHINES_CONFIG[machine_id]["baseline"]["temperature"]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    # Normal baseline zone
    ax.axhspan(base_temp - 1.5, base_temp + 2.0, color="#10b981", alpha=0.15, label="Normal Thermal Band (40.5 - 44°C)")
    ax.axhline(60.0, color="#f59e0b", linestyle="--", linewidth=1.2, label="Warning Threshold (60°C)")
    ax.axhline(68.0, color="#ef4444", linestyle="--", linewidth=1.2, label="Critical Threshold (68°C)")

    # Plot machine temperature
    ax.plot(steps, temps, color="#dc2626", linewidth=2.2, label=f"{machine_id} Telemetry")

    # If recovery trajectory provided, append recovery curve
    if recovery_trajectory:
        last_step = steps[-1]
        rec_steps = [last_step + i * 5 for i in range(len(recovery_trajectory))]
        rec_temps = [r["temperature"] for r in recovery_trajectory]
        ax.plot(rec_steps, rec_temps, color="#2563eb", linestyle="-.", linewidth=2.4, marker="o", label="Post-Recovery Stabilization (CAUSEN AI)")
        ax.axvline(last_step, color="#2563eb", linestyle=":", alpha=0.8, label="Recovery Command Issued")

    ax.set_title(f"CAUSEN AI: Temperature Trajectory & Thermal Stress ({machine_id} - Assembly Line 2)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Simulation Time Steps (30s intervals)", fontsize=11)
    ax.set_ylabel("Operating Temperature (°C)", fontsize=11)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_vibration_profile(
    df: pd.DataFrame,
    machine_id: str,
    output_path: Path = VISUALIZATIONS_DIR / "2_vibration_profile.png"
) -> Path:
    """2. Vibration over time with ISO mechanical limit lines."""
    m_df = df[df["machine_id"] == machine_id].copy().sort_values("step")
    steps = m_df["step"].values
    vibs = m_df["vibration"].values

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    # ISO 10816 mechanical condition zones
    ax.axhspan(0, 1.8, color="#10b981", alpha=0.15, label="Zone A: Good / Normal (< 1.8 mm/s)")
    ax.axhspan(1.8, 2.8, color="#f59e0b", alpha=0.15, label="Zone B: Acceptable / Warning (1.8 - 2.8 mm/s)")
    ax.axhspan(2.8, 6.0, color="#ef4444", alpha=0.15, label="Zone C/D: Unacceptable / Critical (> 2.8 mm/s)")

    ax.plot(steps, vibs, color="#7c3aed", linewidth=2.2, label=f"{machine_id} Vibration Velocity")

    ax.set_title(f"CAUSEN AI: Vibration Profile & Mechanical Wear ({machine_id})", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Simulation Time Steps", fontsize=11)
    ax.set_ylabel("Vibration Velocity RMS (mm/s)", fontsize=11)
    ax.set_ylim(0, max(5.5, max(vibs) + 0.5))
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_production_rate_impact(
    df: pd.DataFrame,
    machine_id: str,
    recovery_trajectory: List[Dict[str, Any]],
    output_path: Path = VISUALIZATIONS_DIR / "3_production_rate_impact.png"
) -> Path:
    """3. Production rate before, during anomaly, and after recovery rerouting."""
    m_df = df[df["machine_id"] == machine_id].copy().sort_values("step")
    steps = list(m_df["step"].values)
    rates = list(m_df["production_rate"].values)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    nominal_rate = MACHINES_CONFIG[machine_id]["baseline"]["throughput_uph"]
    ax.axhline(nominal_rate, color="#10b981", linestyle="--", linewidth=1.5, label=f"Nominal Capacity ({nominal_rate} units/h)")

    ax.plot(steps, rates, color="#0284c7", linewidth=2.2, label=f"{machine_id} Production Throughput")

    if recovery_trajectory:
        last_step = steps[-1]
        rec_steps = [last_step + i * 5 for i in range(len(recovery_trajectory))]
        rec_rates = [r["production_rate"] for r in recovery_trajectory]
        ax.plot(rec_steps, rec_rates, color="#059669", linestyle="-.", linewidth=2.4, marker="s", label="Restored Total Throughput (Line 2 + Rerouted Line 3)")
        ax.axvline(last_step, color="#2563eb", linestyle=":", alpha=0.8, label="Reroute Executed")

    ax.set_title(f"CAUSEN AI: Operational Throughput Impact & Recovery ({machine_id})", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Simulation Time Steps", fontsize=11)
    ax.set_ylabel("Production Rate (units / hour)", fontsize=11)
    ax.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#e2e8f0")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_anomaly_detection_scatter(
    df_detected: pd.DataFrame,
    machine_id: str,
    output_path: Path = VISUALIZATIONS_DIR / "4_anomaly_detection_scatter.png"
) -> Path:
    """4. Anomaly detection scatter plot with Isolation Forest anomaly flags."""
    m_df = df_detected[df_detected["machine_id"] == machine_id].copy().sort_values("step")

    normal_df = m_df[~m_df["is_anomaly"]]
    anom_df = m_df[m_df["is_anomaly"]]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, dpi=300)

    # Panel 1: Temperature & Vibration scatter with Anomaly Flags
    ax1.plot(normal_df["step"], normal_df["temperature"], "o", color="#10b981", alpha=0.7, markersize=5, label="Normal Operation")
    if not anom_df.empty:
        ax1.scatter(anom_df["step"], anom_df["temperature"], color="#ef4444", s=55, marker="D", edgecolor="black", linewidth=0.8, label="Detected Anomaly (Isolation Forest)")
    ax1.set_ylabel("Temperature (°C)", fontsize=10)
    ax1.set_title(f"CAUSEN AI: Isolation Forest Anomaly Detection Timeline ({machine_id})", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True, facecolor="white")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Panel 2: Anomaly Decision Score
    ax2.plot(m_df["step"], m_df["anomaly_score"], color="#3b82f6", linewidth=1.8, label="Outlier Anomaly Score")
    ax2.axhline(0.55, color="#f59e0b", linestyle="--", label="Anomaly Threshold")
    ax2.set_xlabel("Simulation Time Steps", fontsize=10)
    ax2.set_ylabel("Anomaly Score", fontsize=10)
    ax2.legend(loc="upper left", frameon=True, facecolor="white")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_recovery_strategies_comparison(
    simulated_options: List[Dict[str, Any]],
    output_path: Path = VISUALIZATIONS_DIR / "5_recovery_strategies_comparison.png"
) -> Path:
    """5. Comprehensive comparison chart of recovery strategies."""
    names = [opt["name"] for opt in simulated_options]
    loss_scores = [opt["operational_loss_score"] for opt in simulated_options]
    downtimes = [opt["downtime_min"] for opt in simulated_options]
    prod_losses = [opt["production_loss_units"] for opt in simulated_options]
    costs = [opt["maintenance_cost_usd"] for opt in simulated_options]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8), dpi=300)

    colors = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444"]

    # 1. Operational Loss Score (Lower is better)
    bars1 = ax1.bar(names, loss_scores, color=colors, edgecolor="black", width=0.55)
    ax1.set_title("Operational Loss Score (Lower is Better)", fontweight="bold", fontsize=11)
    ax1.set_ylabel("Loss Score (0-100)", fontsize=10)
    ax1.bar_label(bars1, fmt="%.1f", padding=3, fontweight="bold")
    ax1.set_ylim(0, 110)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # 2. Downtime (Minutes)
    bars2 = ax2.bar(names, downtimes, color=colors, edgecolor="black", width=0.55)
    ax2.set_title("Estimated Downtime (Minutes)", fontweight="bold", fontsize=11)
    ax2.set_ylabel("Minutes", fontsize=10)
    ax2.bar_label(bars2, fmt="%.0f min", padding=3)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # 3. Production Loss (Units)
    bars3 = ax3.bar(names, prod_losses, color=colors, edgecolor="black", width=0.55)
    ax3.set_title("Expected Production Loss (Units)", fontweight="bold", fontsize=11)
    ax3.set_ylabel("Units Lost", fontsize=10)
    ax3.bar_label(bars3, fmt="%d", padding=3)
    ax3.grid(True, linestyle=":", alpha=0.6)

    # 4. Maintenance & Disruption Cost (USD)
    bars4 = ax4.bar(names, costs, color=colors, edgecolor="black", width=0.55)
    ax4.set_title("Estimated Cost ($ USD)", fontweight="bold", fontsize=11)
    ax4.set_ylabel("Cost ($)", fontsize=10)
    ax4.bar_label(bars4, fmt="$%d", padding=3)
    ax4.grid(True, linestyle=":", alpha=0.6)

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=12, ha="right", fontsize=9)

    fig.suptitle("CAUSEN AI: Multi-Criteria Recovery Strategy Evaluation", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def generate_interactive_dashboard(
    df: pd.DataFrame,
    df_detected: pd.DataFrame,
    machine_id: str,
    simulated_options: List[Dict[str, Any]],
    output_path: Path = VISUALIZATIONS_DIR / "recovery_dashboard.html"
) -> Path:
    """Generate an interactive HTML Plotly dashboard with all telemetry and strategy comparisons."""
    m_df = df_detected[df_detected["machine_id"] == machine_id].sort_values("step")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f"{machine_id} Operating Temperature (°C)",
            f"{machine_id} Vibration Velocity (mm/s)",
            f"{machine_id} Production Throughput (u/h)",
            "Recovery Strategies - Operational Loss Comparison"
        )
    )

    # 1. Temperature
    fig.add_trace(
        go.Scatter(x=m_df["step"], y=m_df["temperature"], mode="lines+markers", name="Temperature (°C)", line=dict(color="#ef4444", width=2.5)),
        row=1, col=1
    )
    # Highlight anomalies
    anoms = m_df[m_df["is_anomaly"]]
    if not anoms.empty:
        fig.add_trace(
            go.Scatter(x=anoms["step"], y=anoms["temperature"], mode="markers", name="Anomaly Flag", marker=dict(color="#dc2626", size=9, symbol="diamond")),
            row=1, col=1
        )

    # 2. Vibration
    fig.add_trace(
        go.Scatter(x=m_df["step"], y=m_df["vibration"], mode="lines", name="Vibration (mm/s)", line=dict(color="#7c3aed", width=2)),
        row=1, col=2
    )

    # 3. Production Rate
    fig.add_trace(
        go.Scatter(x=m_df["step"], y=m_df["production_rate"], mode="lines", name="Production (u/h)", line=dict(color="#0284c7", width=2)),
        row=2, col=1
    )

    # 4. Strategy Loss Scores
    opt_names = [o["name"] for o in simulated_options]
    opt_scores = [o["operational_loss_score"] for o in simulated_options]
    colors = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444"]

    fig.add_trace(
        go.Bar(x=opt_names, y=opt_scores, marker_color=colors, name="Loss Score", text=opt_scores, textposition="auto"),
        row=2, col=2
    )

    fig.update_layout(
        title_text=f"CAUSEN AI: Industrial Anomaly & Recovery Interactive Dashboard ({machine_id})",
        template="plotly_white",
        height=750,
        showlegend=False
    )

    fig.write_html(str(output_path))
    return output_path


def generate_all_visualizations(
    df: pd.DataFrame,
    df_detected: pd.DataFrame,
    machine_id: str,
    simulated_options: List[Dict[str, Any]],
    recovery_trajectory: List[Dict[str, Any]]
) -> Dict[str, Path]:
    """Generates and returns paths for all 5 static PNG charts and interactive HTML dashboard."""
    p1 = plot_temperature_trajectory(df, machine_id, recovery_trajectory)
    p2 = plot_vibration_profile(df, machine_id)
    p3 = plot_production_rate_impact(df, machine_id, recovery_trajectory)
    p4 = plot_anomaly_detection_scatter(df_detected, machine_id)
    p5 = plot_recovery_strategies_comparison(simulated_options)
    p_html = generate_interactive_dashboard(df, df_detected, machine_id, simulated_options)

    return {
        "temperature_trajectory": p1,
        "vibration_profile": p2,
        "production_rate_impact": p3,
        "anomaly_detection_scatter": p4,
        "recovery_comparison": p5,
        "interactive_dashboard": p_html
    }


if __name__ == "__main__":
    from src.data_simulation import generate_industrial_data
    from src.anomaly_detection import run_anomaly_detection
    from src.recovery_simulation import run_recovery_simulation
    df = generate_industrial_data(n_steps=120)
    df_det, summary = run_anomaly_detection(df)
    sim_res = run_recovery_simulation("M03", {"severity": "CRITICAL", "probable_root_cause": "Cooling"}, {}, summary["peak_record"])
    paths = generate_all_visualizations(df, df_det, "M03", sim_res["options"], sim_res["recovery_trajectory"])
    print("\nVisualizations created:")
    for k, v in paths.items():
        print(f"  • {k}: {v}")
