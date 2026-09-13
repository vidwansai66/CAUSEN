export type DemoState = 'NORMAL' | 'WARNING' | 'CRITICAL' | 'RECOVERY' | 'RECOVERY_COMPLETE';

export interface Machine {
  id: string;
  name: string;
  state: 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'STOPPED' | 'RECOVERING';
  telemetry: {
    throughput: number; // units per hour
    cycleTime: number; // seconds
    temperature: number; // celsius
    vibration: number; // mm/s
    quality: number; // percentage
  };
}

export interface TelemetryTrend {
  timestamp: string;
  value: number;
}

export interface Incident {
  id: string;
  title: string;
  affectedMachineId: string;
  severity: 'NORMAL' | 'WARNING' | 'CRITICAL';
  status: 'ACTIVE' | 'RESOLVING' | 'RESOLVED';
  detectedAt: string;
}

export interface Evidence {
  metric: string;
  change: string; // e.g., "+18%"
  trend: 'UP' | 'DOWN';
  status?: 'ANOMALY' | 'NORMAL';
}

export interface RootCause {
  description: string;
  confidence: number; // 0-100
  evidence: Evidence[];
}

export interface OperationalImpact {
  estimatedDowntimeMinutes: number;
  affectedOrders: number;
  productionLossPercentage: number;
  qualityRisk: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface RecoveryAction {
  id: string;
  title: string;
  description: string;
  type: 'STOP' | 'SLOW' | 'REROUTE' | 'MAINTENANCE' | 'MONITOR';
  expectedProductionLoss: number;
  expectedDowntime: number;
  qualityRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  affectedOrders: number;
  confidence: number;
  rationale: string;
}

export interface WorkflowAction {
  id: string;
  name: string;
  target: string;
  status: 'PENDING' | 'EXECUTING' | 'COMPLETED' | 'FAILED';
  timestamp: string;
}

export interface SystemEvent {
  id: string;
  timestamp: string;
  message: string;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
}
