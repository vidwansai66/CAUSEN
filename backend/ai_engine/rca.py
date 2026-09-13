import sys
import os
from typing import List, Dict, Any

from .models import RCARequest, RCAResult, CauseCandidate, RCAEvidence

def analyze_root_cause(request: RCARequest) -> RCAResult:
    anomaly = request.anomaly
    
    # Fast path for normal operation
    if anomaly.anomaly_score < 0.25:
        return RCAResult(
            machine_id=request.machine_id,
            probable_cause=CauseCandidate(
                name="Normal Operation",
                confidence=1.0,
                evidence=[]
            ),
            evidence=[],
            summary="Machine is operating normally. No root cause analysis required."
        )

    # Convert signals list to dictionary for O(1) lookup
    sig_map = {s.name: s for s in anomaly.signals}

    candidates = []
    
    # 1. Evaluate Cooling System Degradation
    cooling_conf = 0.0
    cooling_evidences = []
    
    temp_sig = sig_map.get("temperature")
    if temp_sig and temp_sig.direction == "HIGH" and temp_sig.contribution > 0:
        cooling_conf += 0.6 * temp_sig.contribution
        cooling_evidences.append(RCAEvidence(
            signal="temperature", 
            observation=f"Temperature is {temp_sig.deviation_percent}% above healthy baseline.",
            importance="HIGH"
        ))
        
    tput_sig = sig_map.get("throughput")
    if tput_sig and tput_sig.direction == "LOW" and tput_sig.contribution > 0:
        cooling_conf += 0.2 * tput_sig.contribution
        cooling_evidences.append(RCAEvidence(
            signal="throughput", 
            observation=f"Throughput is {abs(tput_sig.deviation_percent)}% below baseline.",
            importance="MEDIUM"
        ))
        
    cycle_sig = sig_map.get("cycle_time")
    if cycle_sig and cycle_sig.direction == "HIGH" and cycle_sig.contribution > 0:
        cooling_conf += 0.2 * cycle_sig.contribution
        cooling_evidences.append(RCAEvidence(
            signal="cycle_time", 
            observation=f"Cycle time is significantly elevated.",
            importance="MEDIUM"
        ))
        
    # Check maintenance history
    if request.maintenance_history:
        for record in request.maintenance_history:
            if "cooling" in str(record).lower() or "coolant" in str(record).lower():
                cooling_conf += 0.15
                cooling_evidences.append(RCAEvidence(
                    signal="maintenance",
                    observation="Maintenance history indicates recent or pending cooling system issues.",
                    importance="LOW"
                ))
                break

    cooling_conf = min(1.0, cooling_conf)
    candidates.append(CauseCandidate(name="Cooling System Degradation", confidence=round(cooling_conf, 2), evidence=cooling_evidences))

    # 2. Evaluate Bearing / Mechanical Degradation
    bearing_conf = 0.0
    bearing_evidences = []
    
    vib_sig = sig_map.get("vibration")
    if vib_sig and vib_sig.direction == "HIGH" and vib_sig.contribution > 0:
        bearing_conf += 0.6 * vib_sig.contribution
        bearing_evidences.append(RCAEvidence(
            signal="vibration",
            observation=f"Vibration is {vib_sig.deviation_percent}% above healthy baseline.",
            importance="HIGH"
        ))
        
    if temp_sig and temp_sig.direction == "HIGH" and temp_sig.contribution > 0:
        bearing_conf += 0.2 * temp_sig.contribution
        bearing_evidences.append(RCAEvidence(
            signal="temperature",
            observation="Friction from mechanical wear is causing moderate temperature elevation.",
            importance="MEDIUM"
        ))

    if tput_sig and tput_sig.direction == "LOW" and tput_sig.contribution > 0:
        bearing_conf += 0.2 * tput_sig.contribution
        bearing_evidences.append(RCAEvidence(
            signal="throughput",
            observation="Throughput has dropped secondary to mechanical issues.",
            importance="LOW"
        ))

    if request.maintenance_history:
        for record in request.maintenance_history:
            if "bearing" in str(record).lower() or "spindle" in str(record).lower() or "lubrication" in str(record).lower():
                bearing_conf += 0.15
                bearing_evidences.append(RCAEvidence(
                    signal="maintenance",
                    observation="Maintenance history indicates mechanical or bearing-related issues.",
                    importance="MEDIUM"
                ))
                break

    bearing_conf = min(1.0, bearing_conf)
    candidates.append(CauseCandidate(name="Bearing / Mechanical Degradation", confidence=round(bearing_conf, 2), evidence=bearing_evidences))

    # 3. Evaluate Throughput / Production Degradation
    tput_conf = 0.0
    tput_evidences = []
    
    if tput_sig and tput_sig.direction == "LOW" and tput_sig.contribution > 0:
        tput_conf += 0.5 * tput_sig.contribution
        tput_evidences.append(RCAEvidence(
            signal="throughput",
            observation=f"Throughput is strongly degraded ({abs(tput_sig.deviation_percent)}% below baseline).",
            importance="HIGH"
        ))
        
    if cycle_sig and cycle_sig.direction == "HIGH" and cycle_sig.contribution > 0:
        tput_conf += 0.5 * cycle_sig.contribution
        tput_evidences.append(RCAEvidence(
            signal="cycle_time",
            observation="Cycle time is significantly elevated.",
            importance="HIGH"
        ))
        
    # Penalty: If this is purely a throughput issue, physical signs should NOT be severe.
    # If temperature or vibration are highly anomalous, subtract from throughput confidence.
    if temp_sig and temp_sig.contribution > 0.3:
        tput_conf -= (temp_sig.contribution * 0.5)
    if vib_sig and vib_sig.contribution > 0.3:
        tput_conf -= (vib_sig.contribution * 0.5)
        
    tput_conf = max(0.0, min(1.0, tput_conf))
    candidates.append(CauseCandidate(name="Throughput / Production Degradation", confidence=round(tput_conf, 2), evidence=tput_evidences))

    # Select best candidate
    candidates.sort(key=lambda x: x.confidence, reverse=True)
    best = candidates[0]
    
    if best.confidence < 0.50:
        # Insufficient evidence
        return RCAResult(
            machine_id=request.machine_id,
            probable_cause=CauseCandidate(
                name="Unknown / Insufficient Evidence",
                confidence=round(best.confidence, 2),
                evidence=[]
            ),
            evidence=[],
            summary="Telemetry is abnormal, but there is insufficient correlated evidence to identify a definitive root cause.",
            alternatives=[c for c in candidates if c.confidence >= 0.2]
        )
        
    alternatives = [c for c in candidates[1:] if c.confidence >= 0.2]
    
    summary = f"Multiple correlated signals strongly indicate {best.name.lower()}."
    
    return RCAResult(
        machine_id=request.machine_id,
        probable_cause=best,
        evidence=best.evidence,
        alternatives=alternatives,
        summary=summary
    )
