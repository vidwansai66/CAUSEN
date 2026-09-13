# CAUSEN AI — Intelligent Industrial Decision & Recovery System

**Theme:** AI in Industry Automation  
**Type:** Industrial Prototype & AI Simulation  
**Stack:** Python 3.12, Pandas, NumPy, Scikit-learn (Isolation Forest), Matplotlib, Plotly  

---

## 🏭 Project Overview

**CAUSEN AI** is an intelligent decision-support and closed-loop recovery prototype for automated manufacturing plants. 

Traditional predictive maintenance stops at **anomaly detection** ("A bearing is vibrating"). CAUSEN AI bridges the operational gap between detection and factory remediation by performing:

1. **Continuous Telemetry Simulation**: 10 interconnected machines (`M01` through `M10`) across a multi-stage manufacturing line.
2. **Explainable Anomaly Detection**: Unsupervised `IsolationForest` scoring with z-score multi-channel sensor attribution.
3. **Root Cause Analysis (RCA)**: Multi-sensor fault mode matching with confidence scoring and physical evidence extraction.
4. **Operational Impact Prediction**: Quantitative prediction of downtime, throughput loss, scrap defect surge, and downstream bottleneck delays.
5. **What-If Recovery Simulation**: Evaluates 4 distinct operational recovery strategies (Immediate Maintenance, Speed Derate, Workload Redistribution, and Continue Unchecked).
6. **Multi-Criteria Decision Engine**: Selects the optimal recovery strategy that minimizes the composite Operational Loss Score.
7. **Workflow Automation Simulation**: Closed-loop PLC command dispatch (`REROUTE_WORKLOAD`), digital ticketing (`INC-2049`), supervisor notification, and high-frequency IoT sensor polling.
8. **Engineering Visualizations**: 5 high-resolution analytical charts and an interactive Plotly dashboard.

---

## 📁 Repository Structure

```
causen_ai_simulation/
│
├── data/
│   └── industrial_data.csv          # Generated synthetic 10-machine industrial dataset
│
├── src/
│   ├── __init__.py                  # Package initializer
│   ├── config.py                    # 10 machine baselines, topologies, and thresholds
│   ├── data_simulation.py           # Multi-machine realistic telemetry generator
│   ├── anomaly_detection.py         # Isolation Forest model & sensor contribution scoring
│   ├── root_cause_analysis.py       # Rule-based + AI failure mode inference engine
│   ├── impact_prediction.py         # Operational impact models (loss, downtime, delay)
│   ├── recovery_simulation.py       # What-if simulation (4 strategies & closed-loop trajectory)
│   ├── decision_engine.py           # Multi-criteria optimization & recommendation engine
│   ├── workflow_automation.py       # Simulated industrial ticketing & SCADA command dispatch
│   └── visualizations.py            # Matplotlib & Plotly charting engine
│
├── visualizations/
│   ├── 1_temperature_trajectory.png
│   ├── 2_vibration_profile.png
│   ├── 3_production_rate_impact.png
│   ├── 4_anomaly_detection_scatter.png
│   ├── 5_recovery_strategies_comparison.png
│   └── recovery_dashboard.html      # Interactive web dashboard
│
├── main.py                          # Complete end-to-end CLI demonstration
├── requirements.txt                 # Dependencies
└── README.md                        # Documentation & user guide
```

---

## ⚙️ Quickstart & Setup

### 1. Requirements
Ensure Python 3.10+ is available.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or install directly: `pip install pandas numpy scikit-learn matplotlib plotly`)*

### 3. Run the Demonstration
Execute the flagship demonstration (Machine `M03` - Cooling Degradation & Bearing Wear):

```bash
cd causen_ai_simulation
python main.py
```

### 4. Run Alternative Anomaly Scenarios
Test other industrial fault conditions:

```bash
# Bearing Wear
python main.py --scenario bearing_wear --machine M03

# Motor Overheating
python main.py --scenario motor_overheat --machine M02

# Mechanical Misalignment
python main.py --scenario mechanical_misalignment --machine M08

# Material Stock Defect
python main.py --scenario material_defect --machine M04

# Critical Mechanical Breakdown
python main.py --scenario critical_breakdown --machine M03
```

---

## 📊 Industrial Pipeline & Formulas

### Step 1 — Data Simulation
Generates 10-machine telemetry with micro-stochastic Gaussian fluctuations around calibrated baselines:
- Machine roles: `M01` Raw Material Feed $\to$ `M02` Assembly Line 1 $\to$ `M03` Assembly Line 2 $\to$ `M04` Quality Inspection $\to$ `M05` Packaging $\to$ `M06` Material Transfer $\to$ `M07` Secondary Assembly $\to$ `M08` Finishing $\to$ `M09` Final Inspection $\to$ `M10` Dispatch.

### Step 2 — Isolation Forest Anomaly Detection
- Model: `sklearn.ensemble.IsolationForest(contamination=0.07)`
- Sensor Attribution: For flagged anomalies, computes channel z-score:
  $$z_j = \frac{|x_j - \mu_j|}{\sigma_j}$$
  Channels exceeding $z \ge 2.0$ are flagged as primary contributing physical anomalies.

### Step 3 — Root Cause Analysis (RCA)
Evaluates multivariate combinations against industrial failure signatures:
- **Cooling Degradation / Thermal Stress**: $T \ge 60^\circ\text{C}$ + elevated vibration
- **Bearing Wear**: Vibration $\ge 2.5\text{ mm/s}$ + frictional temperature rise
- **Motor Overheating**: Power $\ge 28\text{ kW}$ + stator temperature spike
- **Shaft Misalignment**: Depressed production $< 1000\text{ u/h}$ + elevated vibration
- **Raw Material Defect**: Scrap defect $> 2.5\%$ while mechanical sensors are normal

### Step 4 — Operational Impact Prediction
- **Production Loss (units)**:
  $$\text{Loss} = \text{Throttled Deficit} + \left(\frac{\text{Downtime}}{60} \times \text{Nominal Rate}\right)$$
- **Downstream Delay (minutes)**:
  $$\text{Delay} = \max(0, \text{Downtime} - \text{Buffer Capacity (10 min)})$$
- **Operational Loss Score (0 to 100)**:
  $$\text{Score} = 0.30 \cdot \text{NormDowntime} + 0.30 \cdot \text{NormProdLoss} + 0.20 \cdot \text{NormDefect} + 0.20 \cdot \text{NormDownstreamDelay}$$

### Step 5 — What-If Recovery Simulation
Compares 4 actionable plant choices:
1. **Option 1 (Immediate Maintenance)**: Stop machine now, replace part ($\text{Downtime}\approx 30\text{m}$, $\text{Loss}\approx 120\text{ units}$, $\text{Score}=35$)
2. **Option 2 (Reduce Machine Speed)**: Derate speed by 40% ($\text{Downtime}\approx 10\text{m}$, $\text{Loss}\approx 110\text{ units}$, $\text{Score}=44$)
3. **Option 3 (Workload Redistribution)**: Reroute queue to backup Line 3 ($\text{Downtime}\approx 5\text{m}$, $\text{Loss}\approx 37\text{ units}$, $\text{Score}=20$) **[RECOMMENDED]**
4. **Option 4 (Ignore Anomaly)**: Continue without intervention ($\text{Downtime}\approx 180\text{m}$, $\text{Loss}\approx 3500\text{ units}$, $\text{Score}=95$)

### Step 6 — Closed-Loop Recovery
Demonstrates the restoration trajectory under Option 3:
- Temperature cools: $71.0^\circ\text{C} \to 60.1^\circ\text{C} \to 44.2^\circ\text{C} \to 42.1^\circ\text{C}$
- Vibration calms: $4.8\text{ mm/s} \to 3.5\text{ mm/s} \to 1.7\text{ mm/s} \to 1.2\text{ mm/s}$
- Total factory throughput restored: $1040 \to 1270 \to 1380 \to 1400\text{ units/h}$

---

## 📈 Visual Outputs

Check `visualizations/` for generated high-res plots:
- `1_temperature_trajectory.png`: Operating temperature vs thermal tolerance bands & recovery
- `2_vibration_profile.png`: Vibration profile vs ISO 10816 safety limits
- `3_production_rate_impact.png`: Throughput impact and recovery restoration
- `4_anomaly_detection_scatter.png`: Isolation Forest anomaly scoring timeline
- `5_recovery_strategies_comparison.png`: Multi-bar comparison across all 4 recovery strategies
- `recovery_dashboard.html`: Interactive browser dashboard (open with any browser)
