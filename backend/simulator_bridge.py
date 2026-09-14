import sys
import os
import time
from datetime import datetime
import numpy as np

# Add simulator to path to import its modules
SIM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simulation"))
if SIM_PATH not in sys.path:
    sys.path.insert(0, SIM_PATH)

from src.config import MACHINES_CONFIG
from src.scenario_engine import generate_telemetry, DISRUPTION_01_COOLING_SYSTEM_DEGRADATION
from src.recovery_simulation import RecoverySimulator
from src.workflow_automation import trigger_workflow_automation

class CausenSimulatorBridge:
    def __init__(self):
        self.rng = np.random.default_rng(42)
        self.reset()

    def reset(self):
        self.step = 0
        self.fault_active = False
        self.fault_machine = "M03"
        self.fault_scenario = DISRUPTION_01_COOLING_SYSTEM_DEGRADATION
        self.recovery_active = False
        self.recovery_step = 0
        self.recovery_trajectory = []
        self.machines = {}
        self.incident = None
        self.rca = None
        self.impact = None
        self.options = []
        self.decision = None
        self.workflow = None
        self.ui_state = "NORMAL"
        self.pending_approval = None
        
        # Populate initial baseline
        self.tick()

    def inject_fault(self, machine_id="M03", fault_type=DISRUPTION_01_COOLING_SYSTEM_DEGRADATION, severity="critical"):
        self.fault_active = True
        self.recovery_active = False
        self.step = 19 if severity == "critical" else -1
        self.fault_machine = machine_id
        self.fault_scenario = fault_type
        self.incident = None
        self.ui_state = "NORMAL"
        self.tick()

    def execute_recovery(self, machine_id: str, action_id: str) -> dict:
        timestamp = datetime.utcnow().isoformat()
        
        if machine_id not in self.machines:
            return {
                "machine_id": machine_id,
                "action_id": action_id,
                "execution_status": "MACHINE_NOT_FOUND",
                "previous_state": self.ui_state,
                "resulting_state": self.ui_state,
                "timestamp": timestamp,
                "message": f"Machine {machine_id} not found.",
                "state_changed": False
            }

        valid_actions = ["NO_ACTION", "STOP_MAINTAIN", "DERATE_SPEED", "REROUTE_WORKLOAD", "CONTINUE_UNCHECKED"]
        if action_id not in valid_actions:
            return {
                "machine_id": machine_id,
                "action_id": action_id,
                "execution_status": "INVALID_ACTION",
                "previous_state": self.ui_state,
                "resulting_state": self.ui_state,
                "timestamp": timestamp,
                "message": f"Invalid action_id {action_id}.",
                "state_changed": False
            }

        if action_id in ["NO_ACTION", "CONTINUE_UNCHECKED"]:
            return {
                "machine_id": machine_id,
                "action_id": action_id,
                "execution_status": "NO_ACTION",
                "previous_state": self.ui_state,
                "resulting_state": self.ui_state,
                "timestamp": timestamp,
                "message": "Action intentionally caused no state mutation.",
                "state_changed": False
            }

        if not self.fault_active or self.fault_machine != machine_id:
            return {
                "machine_id": machine_id,
                "action_id": action_id,
                "execution_status": "REJECTED",
                "previous_state": self.ui_state,
                "resulting_state": self.ui_state,
                "timestamp": timestamp,
                "message": f"No active fault on {machine_id} or recovery already active.",
                "state_changed": False
            }
        
        previous_state = self.ui_state

        # Start recovery loop
        self.recovery_active = True
        self.fault_active = False # Fault stops getting worse
        self.recovery_step = 0
        self.ui_state = "RECOVERY"
        
        # Generate recovery trajectory using the simulator's logic
        sim = RecoverySimulator()
        
        peak_record = self.machines[self.fault_machine]
        peak_dict = peak_record.model_dump()
        peak_dict["production_rate"] = peak_dict["throughput"]
        
        mapped_opt = {"action": action_id}
        
        self.recovery_trajectory = sim.simulate_recovery_trajectory(
            machine_id=self.fault_machine,
            selected_option=mapped_opt,
            incident_readings=peak_dict,
            steps=20
        )

        # Trigger workflow automation to populate actions
        if self.rca and self.decision:
            mock_rca = {
                "severity": "CRITICAL" if self.ui_state == "CRITICAL" else "WARNING",
                "probable_root_cause": self.rca.probable_cause.name,
                "recommended_focus": self.rca.probable_cause.name
            }
            mock_decision = {
                "recommended_action": action_id,
                "action_code": action_id,
                "target_machine": "M07",
                "target_line": "LINE-3"
            }
            self.workflow = trigger_workflow_automation(self.fault_machine, mock_rca, mock_decision)

        return {
            "machine_id": machine_id,
            "action_id": action_id,
            "execution_status": "EXECUTED",
            "previous_state": previous_state,
            "resulting_state": self.ui_state,
            "timestamp": timestamp,
            "message": f"Recovery action {action_id} executing.",
            "state_changed": True
        }

    def _resolve_global_state(self):
        if self.ui_state in ["RECOVERY", "RECOVERY_COMPLETE"]:
            return self.ui_state
            
        highest_severity = "NORMAL"
        for data in self.machines.values():
            st = data.state
            if st == "CRITICAL":
                highest_severity = "CRITICAL"
            elif st == "WARNING" and highest_severity != "CRITICAL":
                highest_severity = "WARNING"
                
        return highest_severity

    def tick(self):
        self.step += 1
        
        # Update each machine
        for m_id, cfg in MACHINES_CONFIG.items():
            if m_id == self.fault_machine:
                if self.recovery_active:
                    # Recovery is active, we just generate normal baseline for now 
                    # and overlay trajectory below
                    reading = generate_telemetry(m_id, self.step, self.rng)
                elif self.fault_active:
                    severity = min(1.0, self.step / 20.0)
                    reading = generate_telemetry(m_id, self.step, self.rng, active_scenario=self.fault_scenario, severity=severity)
                else:
                    reading = generate_telemetry(m_id, self.step, self.rng)
            else:
                reading = generate_telemetry(m_id, self.step, self.rng)
                
            if m_id == self.fault_machine and self.recovery_active:
                if self.recovery_step < len(self.recovery_trajectory):
                    traj_point = self.recovery_trajectory[self.recovery_step]
                    reading.temperature = traj_point["temperature"]
                    reading.vibration = traj_point["vibration"]
                    reading.throughput = traj_point["production_rate"]
                    reading.defect_rate = traj_point["defect_rate"]
                    reading.state = traj_point["state"]
                else:
                    self.ui_state = "RECOVERY_COMPLETE"
            
            self.machines[m_id] = reading

        # Apply downstream starvation modeling based on upstream actual throughput ratio
        for m_id, cfg in MACHINES_CONFIG.items():
            reading = self.machines[m_id]
            upstream_machines = [u_id for u_id, u_cfg in MACHINES_CONFIG.items() if m_id in u_cfg["downstream"]]
            
            if upstream_machines:
                ratios = []
                for u_id in upstream_machines:
                    if u_id in self.machines:
                        u_reading = self.machines[u_id]
                        u_baseline = MACHINES_CONFIG[u_id]["baseline"]["throughput_uph"]
                        # Ratio is bounded to a max of 1.0 so noise spikes don't artificially boost downstream
                        ratio = min(1.0, u_reading.throughput / u_baseline)
                        ratios.append(ratio)
                
                if ratios:
                    bottleneck_ratio = min(ratios)
                    
                    if bottleneck_ratio < 1.0:
                        reading.throughput = round(reading.throughput * bottleneck_ratio, 1)
                        
                        if reading.throughput > 0:
                            base_cfg = MACHINES_CONFIG[m_id]["baseline"]
                            reading.cycle_time = round(base_cfg["cycle_time"] * (base_cfg["throughput_uph"] / reading.throughput), 1)
                        else:
                            reading.cycle_time = 0.0

        if self.recovery_active:
            self.recovery_step += 1
            
        self.ui_state = self._resolve_global_state()

        # Run new AI Engine on fault machine to update CAUSEN state
        if self.fault_active or self.ui_state in ["WARNING", "CRITICAL"]:
            m03_state = self.machines[self.fault_machine].model_dump()
            
            from ai_engine.orchestrator import run_ai_pipeline
            from ai_engine.models import PipelineRequest
            
            req = PipelineRequest(machine_id=self.fault_machine, telemetry=m03_state)
            analysis = run_ai_pipeline(req)
            
            self.rca = analysis.rca
            self.impact = analysis.impact
            self.options = analysis.recovery_simulations
            self.decision = analysis.decision
                
            if self.ui_state in ["WARNING", "CRITICAL", "RECOVERY", "RECOVERY_COMPLETE"]:
                if not self.incident:
                    title_map = {
                        "DISRUPTION_01_COOLING_SYSTEM_DEGRADATION": "COOLING SYSTEM DEGRADATION",
                        "DISRUPTION_02_BEARING_DEGRADATION": "SPINDLE BEARING WEAR",
                        "DISRUPTION_03_THROUGHPUT_DEGRADATION": "THROUGHPUT DEGRADATION"
                    }
                    display_title = title_map.get(self.fault_scenario, "SYSTEM ANOMALY")
                    
                    self.incident = {
                        "id": "INC-2049",
                        "title": f"{self.fault_machine} — {display_title}",
                        "affectedMachineId": self.fault_machine,
                        "severity": self.ui_state if self.ui_state in ["WARNING", "CRITICAL"] else "WARNING",
                        "status": "ACTIVE",
                        "detectedAt": datetime.utcnow().strftime("%H:%M:%S")
                    }
                elif self.ui_state in ["WARNING", "CRITICAL"]:
                    self.incident["severity"] = self.ui_state

    def get_frontend_state(self):
        # Map internal state to frontend models
        mapped_machines = []
        for m_id, data in self.machines.items():
            
            st = "HEALTHY"
            if data.state in ["WARNING", "CRITICAL", "RECOVERING"]:
                st = data.state
            elif data.state == "RECOVERED/HEALTHY":
                st = "HEALTHY"

            mapped_machines.append({
                "id": m_id,
                "name": data.machine_name,
                "state": st,
                "telemetry": {
                    "throughput": data.throughput,
                    "cycleTime": data.cycle_time,
                    "temperature": data.temperature,
                    "vibration": data.vibration,
                    "quality": data.quality,
                    "power_consumption": getattr(data, "power_consumption", 20.0),
                    "defect_rate": getattr(data, "defect_rate", 0.5)
                },
                "safe_limits": MACHINES_CONFIG[m_id].get("safe_limits", {})
            })

        mapped_rca = None
        if self.rca:
            mapped_rca = {
                "description": self.rca.probable_cause.name,
                "confidence": round(self.rca.probable_cause.confidence * 100, 1),
                "evidence": []
            }
            
            m_id = self.fault_machine
            if m_id in self.machines and m_id in MACHINES_CONFIG:
                m_data = self.machines[m_id]
                baseline = MACHINES_CONFIG[m_id]["baseline"]
                
                for ev in self.rca.evidence:
                    ev_lower = ev.observation.lower()
                    metric_name = "Telemetry"
                    trend = "UP"
                    
                    if "temperature" in ev_lower:
                        metric_name = "Temperature"
                        trend = "UP" if m_data.temperature > baseline["temperature"] else "DOWN"
                    elif "vibration" in ev_lower:
                        metric_name = "Vibration"
                        trend = "UP" if m_data.vibration > baseline["vibration"] else "DOWN"
                    elif "throughput" in ev_lower or "production" in ev_lower:
                        metric_name = "Throughput"
                        trend = "UP" if m_data.throughput > baseline["throughput_uph"] else "DOWN"
                    elif "defect" in ev_lower or "scrap" in ev_lower:
                        metric_name = "Defect Rate"
                        trend = "UP" if m_data.defect_rate > baseline["defect_rate"] else "DOWN"
                    elif "cycle" in ev_lower:
                        metric_name = "Cycle Time"
                        trend = "UP" if m_data.cycle_time > baseline["cycle_time"] else "DOWN"

                    mapped_rca["evidence"].append({
                        "metric": metric_name,
                        "change": ev.observation,
                        "trend": trend,
                        "status": "ANOMALY"
                    })
        
        mapped_impact = None
        if self.impact:
            mapped_impact = {
                "estimatedDowntimeMinutes": self.impact.impact.downtime.projected_minutes or self.impact.impact.downtime.observed_minutes,
                "affectedOrders": self.impact.impact.orders.affected_orders or 0,
                "productionLossPercentage": round(self.impact.impact.production.loss_rate * 100, 1) if self.impact.impact.production.loss_rate else 0.0,
                "qualityRisk": self.impact.impact.quality.impact.upper() if self.impact.impact.quality.impact.upper() in ["LOW", "MEDIUM", "HIGH"] else "HIGH"
            }
            
        mapped_actions = []
        if self.decision and self.decision.ranked_options:
            for opt in self.decision.ranked_options:
                sim_opt = next((s for s in self.options if s.action.action_id == opt.action_id), None)
                expected_loss = round(sim_opt.after.production_loss_rate * 100, 1) if sim_opt and sim_opt.after.production_loss_rate else 0.0
                expected_dt = sim_opt.after.downtime_risk * 100 if sim_opt else 0.0
                
                title = opt.action_id.replace("_", " ")
                mapped_actions.append({
                    "id": f"ACT-{opt.action_id}",
                    "title": "REROUTE WORKLOAD → LINE 3" if "REROUTE" in opt.action_id else title,
                    "description": opt.production_tradeoff,
                    "type": "STOP" if "STOP" in opt.action_id else "SLOW" if "DERATE" in opt.action_id else "REROUTE" if "REROUTE" in opt.action_id else "MAINTENANCE",
                    "expectedProductionLoss": expected_loss,
                    "expectedDowntime": round(expected_dt, 1),
                    "qualityRisk": opt.residual_risk.upper() if opt.residual_risk.upper() in ["LOW", "MEDIUM", "HIGH", "CRITICAL"] else "HIGH",
                    "affectedOrders": 0,
                    "confidence": round(opt.confidence * 100, 1),
                    "rationale": opt.reason
                })

        mapped_workflow = []
        if self.workflow:
            for i, act in enumerate(self.workflow["actions_log"]):
                mapped_workflow.append({
                    "id": str(i),
                    "name": act["action"],
                    "target": "System",
                    "status": "COMPLETED",
                    "timestamp": datetime.utcnow().strftime("%H:%M:%S")
                })
                
        if self.ui_state == "RECOVERY":
            if self.incident:
                self.incident["status"] = "RESOLVING"
        elif self.ui_state == "RECOVERY_COMPLETE":
            if self.incident:
                self.incident["status"] = "RESOLVED"
                self.incident["severity"] = "NORMAL"

        return {
            "demoState": self.ui_state,
            "machines": mapped_machines,
            "incident": self.incident,
            "rootCause": mapped_rca,
            "impact": mapped_impact,
            "recoveryActions": mapped_actions,
            "workflowActivity": mapped_workflow,
            "pending_approval": self.pending_approval
        }

bridge = CausenSimulatorBridge()
