from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SignalEvidence(BaseModel):
    name: str
    baseline: float
    current: float
    deviation_percent: float
    direction: str
    contribution: float

class AnomalyResult(BaseModel):
    machine_id: str
    timestamp: str
    is_anomaly: bool
    anomaly_score: float
    severity: str
    signals: List[SignalEvidence]
    summary: str

class AnomalyRequest(BaseModel):
    machine_id: str
    telemetry: dict

class RCAEvidence(BaseModel):
    signal: str
    observation: str
    importance: str

class CauseCandidate(BaseModel):
    name: str
    confidence: float
    evidence: List[RCAEvidence] = []

class RCAResult(BaseModel):
    machine_id: str
    probable_cause: CauseCandidate
    evidence: List[RCAEvidence]
    contributing_factors: List[str] = []
    alternatives: List[CauseCandidate] = []
    summary: str

class RCARequest(BaseModel):
    machine_id: str
    telemetry: dict
    anomaly: AnomalyResult
    maintenance_history: Optional[List[dict]] = None

class ImpactProduction(BaseModel):
    baseline_throughput: float
    current_throughput: Optional[float] = None
    loss_rate: Optional[float] = None
    estimated_loss_per_hour: Optional[float] = None

class ImpactDowntime(BaseModel):
    observed_minutes: float
    risk_score: float
    projected_minutes: Optional[float]

class ImpactQuality(BaseModel):
    current_quality: float
    baseline_quality: float
    impact: str

class ImpactOrders(BaseModel):
    affected_capacity: float
    affected_orders: Optional[int] = None

class ImpactFinancial(BaseModel):
    estimated_loss: Optional[float] = None
    currency: Optional[str] = None

class ImpactDetails(BaseModel):
    production: ImpactProduction
    downtime: ImpactDowntime
    quality: ImpactQuality
    orders: ImpactOrders
    financial: ImpactFinancial

class ImpactResult(BaseModel):
    machine_id: str
    impact: ImpactDetails
    confidence: float
    evidence: List[str]
    assumptions: List[str]
    explanation: str

class ImpactRequest(BaseModel):
    machine_id: str
    telemetry: dict
    anomaly: AnomalyResult
    rca: RCAResult

# ---------------------------------------------------------
# RECOVERY MODELS (PART 6)
# ---------------------------------------------------------

class RecoveryAction(BaseModel):
    action_id: str
    name: str
    description: str

class RecoverySimulationRequest(BaseModel):
    machine_id: str
    telemetry: Dict[str, Any]
    anomaly: AnomalyResult
    rca: RCAResult
    impact: ImpactResult
    action: RecoveryAction

class RecoveryBeforeAfterState(BaseModel):
    predicted_telemetry: Optional[Dict[str, Any]] = None
    anomaly_score: float
    anomaly_severity: str
    production_loss_rate: Optional[float] = None
    downtime_risk: float

class RecoveryDelta(BaseModel):
    anomaly_score_change: float
    production_loss_change: Optional[float] = None
    downtime_risk_change: float
    throughput_change: Optional[float] = None

class RecoverySimulationResult(BaseModel):
    machine_id: str
    action: RecoveryAction
    before: RecoveryBeforeAfterState
    after: RecoveryBeforeAfterState
    delta: RecoveryDelta
    recovery_effectiveness: float
    confidence: float
    assumptions: List[str]
    evidence: List[str]
    explanation: str

# ---------------------------------------------------------
# DECISION MODELS (PART 7)
# ---------------------------------------------------------

class DecisionRequest(BaseModel):
    machine_id: str
    telemetry: Dict[str, Any]
    anomaly: AnomalyResult
    rca: RCAResult
    impact: ImpactResult
    recovery_options: List[RecoverySimulationResult]

class RankedOption(BaseModel):
    action_id: str
    rank: int
    score: float
    effectiveness: float
    confidence: float
    residual_risk: str
    production_tradeoff: str
    reason: str

class DecisionDecision(BaseModel):
    recommended_action: str
    recommendation: str
    decision_confidence: float

class RejectedAlternative(BaseModel):
    action_id: str
    reason: str

class DecisionResult(BaseModel):
    machine_id: str
    decision: DecisionDecision
    risk_level: str
    ranked_options: List[RankedOption]
    why_this_action: List[str]
    rejected_alternatives: List[RejectedAlternative]
    operational_tradeoffs: List[str]
    evidence: List[str]
    assumptions: List[str]

# ---------------------------------------------------------
# ORCHESTRATOR MODELS (PART 8)
# ---------------------------------------------------------

class PipelineRequest(BaseModel):
    machine_id: str
    telemetry: Dict[str, Any]

class PipelineResult(BaseModel):
    machine_id: str
    anomaly: AnomalyResult
    rca: RCAResult
    impact: ImpactResult
    recovery_simulations: List[RecoverySimulationResult]
    decision: DecisionResult

