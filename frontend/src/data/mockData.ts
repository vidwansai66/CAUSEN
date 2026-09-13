import type { DemoState, Machine, Incident, RootCause, RecoveryAction, OperationalImpact } from '../types';

export const mockMachines: Record<DemoState, Machine[]> = {
  NORMAL: [
    { id: 'M01', name: 'Material Feed', state: 'HEALTHY', telemetry: { temperature: 42, vibration: 1.2, cycleTime: 45, throughput: 1200, quality: 99.8 } },
    { id: 'M02', name: 'Assembly Alpha', state: 'HEALTHY', telemetry: { temperature: 45, vibration: 1.5, cycleTime: 42, throughput: 1180, quality: 99.5 } },
    { id: 'M03', name: 'Assembly Beta', state: 'HEALTHY', telemetry: { temperature: 43, vibration: 1.4, cycleTime: 45, throughput: 1150, quality: 99.7 } },
    { id: 'M04', name: 'Quality Scan', state: 'HEALTHY', telemetry: { temperature: 38, vibration: 0.8, cycleTime: 30, throughput: 1150, quality: 99.9 } },
    { id: 'M05', name: 'Packaging', state: 'HEALTHY', telemetry: { temperature: 40, vibration: 1.0, cycleTime: 45, throughput: 1150, quality: 99.9 } },
  ],
  WARNING: [
    { id: 'M01', name: 'Material Feed', state: 'HEALTHY', telemetry: { temperature: 42, vibration: 1.2, cycleTime: 45, throughput: 1200, quality: 99.8 } },
    { id: 'M02', name: 'Assembly Alpha', state: 'HEALTHY', telemetry: { temperature: 45, vibration: 1.5, cycleTime: 42, throughput: 1180, quality: 99.5 } },
    { id: 'M03', name: 'Assembly Beta', state: 'WARNING', telemetry: { temperature: 55, vibration: 2.8, cycleTime: 48, throughput: 1090, quality: 98.2 } },
    { id: 'M04', name: 'Quality Scan', state: 'HEALTHY', telemetry: { temperature: 38, vibration: 0.8, cycleTime: 30, throughput: 1090, quality: 99.9 } },
    { id: 'M05', name: 'Packaging', state: 'HEALTHY', telemetry: { temperature: 40, vibration: 1.0, cycleTime: 45, throughput: 1090, quality: 99.9 } },
  ],
  CRITICAL: [
    { id: 'M01', name: 'Material Feed', state: 'HEALTHY', telemetry: { temperature: 42, vibration: 1.2, cycleTime: 45, throughput: 1200, quality: 99.8 } },
    { id: 'M02', name: 'Assembly Alpha', state: 'HEALTHY', telemetry: { temperature: 45, vibration: 1.5, cycleTime: 42, throughput: 1180, quality: 99.5 } },
    { id: 'M03', name: 'Assembly Beta', state: 'CRITICAL', telemetry: { temperature: 71, vibration: 4.8, cycleTime: 61, throughput: 1040, quality: 96.8 } },
    { id: 'M04', name: 'Quality Scan', state: 'HEALTHY', telemetry: { temperature: 38, vibration: 0.8, cycleTime: 30, throughput: 1040, quality: 99.9 } },
    { id: 'M05', name: 'Packaging', state: 'HEALTHY', telemetry: { temperature: 40, vibration: 1.0, cycleTime: 45, throughput: 1040, quality: 99.9 } },
  ],
  RECOVERY: [
    { id: 'M01', name: 'Material Feed', state: 'HEALTHY', telemetry: { temperature: 42, vibration: 1.2, cycleTime: 45, throughput: 1200, quality: 99.8 } },
    { id: 'M02', name: 'Assembly Alpha', state: 'HEALTHY', telemetry: { temperature: 45, vibration: 1.5, cycleTime: 42, throughput: 1180, quality: 99.5 } },
    { id: 'M03', name: 'Assembly Beta', state: 'RECOVERING', telemetry: { temperature: 65, vibration: 3.5, cycleTime: 55, throughput: 1080, quality: 97.5 } },
    { id: 'M04', name: 'Quality Scan', state: 'HEALTHY', telemetry: { temperature: 38, vibration: 0.8, cycleTime: 30, throughput: 1080, quality: 99.9 } },
    { id: 'M05', name: 'Packaging', state: 'HEALTHY', telemetry: { temperature: 40, vibration: 1.0, cycleTime: 45, throughput: 1080, quality: 99.9 } },
  ],
  RECOVERY_COMPLETE: [
    { id: 'M01', name: 'Material Feed', state: 'HEALTHY', telemetry: { temperature: 42, vibration: 1.2, cycleTime: 45, throughput: 1200, quality: 99.8 } },
    { id: 'M02', name: 'Assembly Alpha', state: 'HEALTHY', telemetry: { temperature: 45, vibration: 1.5, cycleTime: 42, throughput: 1180, quality: 99.5 } },
    { id: 'M03', name: 'Assembly Beta', state: 'HEALTHY', telemetry: { temperature: 44, vibration: 1.5, cycleTime: 45, throughput: 1150, quality: 99.7 } },
    { id: 'M04', name: 'Quality Scan', state: 'HEALTHY', telemetry: { temperature: 38, vibration: 0.8, cycleTime: 30, throughput: 1150, quality: 99.9 } },
    { id: 'M05', name: 'Packaging', state: 'HEALTHY', telemetry: { temperature: 40, vibration: 1.0, cycleTime: 45, throughput: 1150, quality: 99.9 } },
  ]
};

export const mockIncident: Record<DemoState, Incident | null> = {
  NORMAL: null,
  WARNING: {
    id: 'INC-2049',
    title: 'M03 — THROUGHPUT DEGRADATION',
    status: 'ACTIVE',
    severity: 'WARNING',
    affectedMachineId: 'M03',
    detectedAt: '10:41:12'
  },
  CRITICAL: {
    id: 'INC-2049',
    title: 'M03 — THROUGHPUT DEGRADATION',
    status: 'ACTIVE',
    severity: 'CRITICAL',
    affectedMachineId: 'M03',
    detectedAt: '10:41:12'
  },
  RECOVERY: {
    id: 'INC-2049',
    title: 'M03 — THROUGHPUT DEGRADATION',
    status: 'RESOLVING',
    severity: 'WARNING',
    affectedMachineId: 'M03',
    detectedAt: '10:41:12'
  },
  RECOVERY_COMPLETE: {
    id: 'INC-2049',
    title: 'M03 — THROUGHPUT DEGRADATION',
    status: 'RESOLVED',
    severity: 'NORMAL',
    affectedMachineId: 'M03',
    detectedAt: '10:41:12'
  }
};

export const mockRootCause: RootCause = {
  description: 'Cooling system degradation',
  confidence: 87,
  evidence: [
    { metric: 'Temperature', change: '42°C → 71°C', trend: 'UP' },
    { metric: 'Vibration', change: '1.4 → 4.8 mm/s', trend: 'UP' },
    { metric: 'Cycle Time', change: '45s → 61s', trend: 'UP' },
    { metric: 'Quality', change: '99.7% → 96.8%', trend: 'DOWN' },
    { metric: 'Throughput', change: '1150 → 1040 u/h', trend: 'DOWN' }
  ]
};

export const mockImpact: OperationalImpact = {
  productionLossPercentage: 6.2,
  estimatedDowntimeMinutes: 18,
  qualityRisk: 'MEDIUM',
  affectedOrders: 12
};

export const mockRecoveryActions: RecoveryAction[] = [
  {
    id: 'ACT-001',
    title: 'STOP MACHINE',
    type: 'STOP',
    description: 'Immediately halt M03 to prevent hardware damage.',
    expectedProductionLoss: 14.5,
    expectedDowntime: 45,
    qualityRisk: 'LOW',
    affectedOrders: 28,
    confidence: 99,
    rationale: 'Stops production completely. Highest downtime, but protects hardware.'
  },
  {
    id: 'ACT-002',
    title: 'SLOW PRODUCTION',
    type: 'SLOW',
    description: 'Reduce throughput by 30% to stabilize temperatures.',
    expectedProductionLoss: 8.5,
    expectedDowntime: 0,
    qualityRisk: 'HIGH',
    affectedOrders: 15,
    confidence: 65,
    rationale: 'May not completely prevent overheating, risks producing defective parts.'
  },
  {
    id: 'ACT-003',
    title: 'REROUTE WORKLOAD → LINE 3',
    type: 'REROUTE',
    description: 'Divert critical orders to Line 3 while M03 undergoes maintenance.',
    expectedProductionLoss: 2.1,
    expectedDowntime: 14,
    qualityRisk: 'LOW',
    affectedOrders: 3,
    confidence: 91,
    rationale: 'Rerouting minimizes expected production loss while avoiding immediate machine shutdown. Line 3 has 30% available capacity.'
  },
  {
    id: 'ACT-004',
    title: 'MAINTENANCE',
    type: 'MAINTENANCE',
    description: 'Dispatch engineer for live repair while running.',
    expectedProductionLoss: 5.5,
    expectedDowntime: 10,
    qualityRisk: 'MEDIUM',
    affectedOrders: 10,
    confidence: 55,
    rationale: 'High risk of failure during live repair. Not recommended for cooling systems.'
  }
];

export const mockWorkflowActivity: Record<DemoState, any[]> = {
  NORMAL: [
    { id: '1', time: '08:00:00', type: 'info', message: 'System initialization complete.' },
    { id: '2', time: '09:15:30', type: 'info', message: 'Routine diagnostic passed on M05.' }
  ],
  WARNING: [
    { id: '1', time: '10:41:00', type: 'warning', message: 'Vibration increase detected on M03.' }
  ],
  CRITICAL: [
    { id: '1', time: '10:41:12', type: 'critical', message: 'Anomaly detected — M03' },
    { id: '2', time: '10:41:18', type: 'critical', message: 'Incident classified — CRITICAL' },
    { id: '3', time: '10:41:22', type: 'info', message: 'Evidence correlation completed' },
    { id: '4', time: '10:41:25', type: 'warning', message: 'Root cause identified — Cooling system degradation' },
    { id: '5', time: '10:41:27', type: 'info', message: 'Recovery simulations generated' }
  ],
  RECOVERY: [
    { id: '1', time: '10:41:12', type: 'critical', message: 'Anomaly detected — M03' },
    { id: '2', time: '10:41:18', type: 'critical', message: 'Incident classified — CRITICAL' },
    { id: '3', time: '10:41:22', type: 'info', message: 'Evidence correlation completed' },
    { id: '4', time: '10:41:25', type: 'warning', message: 'Root cause identified — Cooling system degradation' },
    { id: '5', time: '10:41:27', type: 'info', message: 'Recovery simulations generated' },
    { id: '6', time: '10:41:31', type: 'info', message: 'Operator selected Reroute Workload → Line 3' },
    { id: '7', time: '10:41:35', type: 'info', message: 'Workload redistribution started' }
  ],
  RECOVERY_COMPLETE: [
    { id: '4', time: '10:41:25', type: 'warning', message: 'Root cause identified — Cooling system degradation' },
    { id: '5', time: '10:41:27', type: 'info', message: 'Recovery simulations generated' },
    { id: '6', time: '10:41:31', type: 'info', message: 'Operator selected Reroute Workload → Line 3' },
    { id: '7', time: '10:41:35', type: 'info', message: 'Workload redistribution started' },
    { id: '8', time: '10:42:04', type: 'success', message: 'Recovery completed' }
  ]
};
