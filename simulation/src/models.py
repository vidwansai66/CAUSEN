from pydantic import BaseModel, Field
from typing import List, Optional

class MaintenanceRecord(BaseModel):
    date: str
    type: str
    description: str

class MachineTelemetry(BaseModel):
    machine_id: str
    machine_name: str
    line_id: str
    state: str = "HEALTHY"
    timestamp: str
    step: int
    throughput: float
    cycle_time: float
    temperature: float
    vibration: float
    pressure: float
    power_consumption: float
    quality: float
    defect_rate: float
    maintenance_history: List[MaintenanceRecord] = Field(default_factory=list)
    active_fault: Optional[str] = None
    production_orders: Optional[List[str]] = Field(default_factory=list)

class ScenarioDefinition(BaseModel):
    scenario_id: str
    name: str
    description: str
