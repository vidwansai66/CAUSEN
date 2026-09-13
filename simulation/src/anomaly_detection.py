"""
CAUSEN AI: Anomaly Detection Engine
Uses Isolation Forest to detect industrial equipment anomalies.
Provides explainable feature attribution identifying the specific sensors
responsible for abnormal operational deviations.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from src.config import FEATURE_COLUMNS, MACHINES_CONFIG


class IndustrialAnomalyDetector:
    """
    Explainable Industrial Anomaly Detector powered by Isolation Forest
    with sensor contribution scoring.
    """

    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_cols = FEATURE_COLUMNS
        self.baseline_stats: Dict[str, Dict[str, Tuple[float, float]]] = {}
        self.is_fitted = False

    def fit(self, baseline_df: pd.DataFrame) -> "IndustrialAnomalyDetector":
        """
        Fit detector on normal factory telemetry and compute baseline distributions.
        """
        # Store mean & std per machine for explainability
        for m_id in baseline_df["machine_id"].unique():
            m_sub = baseline_df[baseline_df["machine_id"] == m_id]
            self.baseline_stats[m_id] = {}
            for col in self.feature_cols:
                mean_val = float(m_sub[col].mean())
                std_val = float(m_sub[col].std())
                self.baseline_stats[m_id][col] = (mean_val, max(1e-4, std_val))

        # Scale features and fit Isolation Forest
        X = baseline_df[self.feature_cols].values
        self.scaler.fit(X)
        self.model.fit(self.scaler.transform(X))
        self.is_fitted = True
        return self

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run anomaly detection on telemetry dataset.
        Appends 'is_anomaly', 'anomaly_score', and 'contributing_sensors'.
        """
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetector must be fitted before calling detect().")

        df = df.copy()
        X = df[self.feature_cols].values
        X_scaled = self.scaler.transform(X)

        # Isolation forest predictions: 1 for normal, -1 for anomaly
        preds = self.model.predict(X_scaled)
        # raw decision function: negative values indicate outliers
        scores = -self.model.score_samples(X_scaled)

        df["is_anomaly"] = (preds == -1)
        df["anomaly_score"] = np.round(scores, 4)

        # Compute sensor attribution for anomalous records
        contributions = []
        for idx, row in df.iterrows():
            if not row["is_anomaly"]:
                contributions.append([])
                continue

            m_id = row["machine_id"]
            stats = self.baseline_stats.get(m_id, {})
            channel_deviations = []

            for col in self.feature_cols:
                observed = row[col]
                mean_val, std_val = stats.get(col, (observed, 1.0))
                z_score = abs(observed - mean_val) / std_val
                if z_score >= 2.0:
                    channel_deviations.append({
                        "sensor": col,
                        "observed": observed,
                        "baseline_mean": round(mean_val, 2),
                        "z_score": round(z_score, 2),
                        "delta": round(observed - mean_val, 2)
                    })

            # Sort by highest deviation
            channel_deviations.sort(key=lambda x: x["z_score"], reverse=True)
            contributions.append(channel_deviations)

        df["contributing_sensors"] = contributions
        return df

    def analyze_results(self, df_detected: pd.DataFrame) -> Dict[str, Any]:
        """
        Summarize anomaly detection findings for executive report and root-cause inputs.
        """
        total_records = len(df_detected)
        anomalies_df = df_detected[df_detected["is_anomaly"]].copy()
        num_anomalies = len(anomalies_df)

        if num_anomalies == 0:
            return {
                "total_records": total_records,
                "num_anomalies": 0,
                "anomaly_rate_pct": 0.0,
                "affected_machines": [],
                "primary_machine": None,
                "peak_anomaly_record": None,
                "top_contributing_sensors": []
            }

        # Count anomalies by machine
        machine_counts = anomalies_df["machine_id"].value_counts().to_dict()
        
        # Primary machine has highest count of anomalies and peak score
        primary_machine = anomalies_df.groupby("machine_id")["anomaly_score"].mean().idxmax()
        
        # Extract peak anomaly record for primary machine
        primary_anomalies = anomalies_df[anomalies_df["machine_id"] == primary_machine]
        peak_row = primary_anomalies.loc[primary_anomalies["anomaly_score"].idxmax()]

        return {
            "total_records": total_records,
            "num_anomalies": num_anomalies,
            "anomaly_rate_pct": round((num_anomalies / total_records) * 100, 2),
            "affected_machines": list(machine_counts.keys()),
            "anomalies_by_machine": machine_counts,
            "primary_machine": primary_machine,
            "primary_machine_name": MACHINES_CONFIG[primary_machine]["name"],
            "first_anomaly_timestamp": str(anomalies_df.iloc[0]["timestamp"]),
            "peak_anomaly_timestamp": str(peak_row["timestamp"]),
            "peak_anomaly_score": float(peak_row["anomaly_score"]),
            "peak_record": peak_row.to_dict(),
            "top_contributing_sensors": peak_row["contributing_sensors"]
        }


def run_anomaly_detection(df: pd.DataFrame, baseline_steps: int = 40) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience runner: fits on normal initial steps, detects on full dataset."""
    baseline_df = df[df["step"] < baseline_steps].copy()
    detector = IndustrialAnomalyDetector(contamination=0.07, random_state=42)
    detector.fit(baseline_df)
    df_detected = detector.detect(df)
    summary = detector.analyze_results(df_detected)
    return df_detected, summary


if __name__ == "__main__":
    from src.data_simulation import generate_industrial_data
    df = generate_industrial_data(n_steps=120)
    df_detected, summary = run_anomaly_detection(df)
    print("\n--- ANOMALY DETECTION SUMMARY ---")
    print(f"Total records: {summary['total_records']}")
    print(f"Anomalies detected: {summary['num_anomalies']} ({summary['anomaly_rate_pct']}%)")
    print(f"Primary affected machine: {summary['primary_machine']} - {summary['primary_machine_name']}")
    print("Contributing sensors at peak:")
    for s in summary["top_contributing_sensors"]:
        print(f"  • {s['sensor']}: observed={s['observed']}, baseline={s['baseline_mean']}, z-score={s['z_score']}")
