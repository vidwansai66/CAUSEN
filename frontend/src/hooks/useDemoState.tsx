import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { API_BASE_URL } from '../config';
import type { DemoState, Machine, Incident, RootCause, OperationalImpact, RecoveryAction, WorkflowAction } from '../types';

interface DemoContextType {
  state: DemoState;
  setState: (state: DemoState) => void;
  selectedActionId: string | null;
  executeRecoveryAction: (actionId: string) => void;
  injectFault: (machineId: string, faultType: string) => void;
  resetFactory: () => void;
  
  // API State
  machines: Machine[];
  incident: Incident | null;
  rootCause: RootCause | null;
  impact: OperationalImpact | null;
  recoveryActions: RecoveryAction[];
  workflowActivity: WorkflowAction[];
  connectionStatus: 'CONNECTING' | 'CONNECTED' | 'OFFLINE';
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export function DemoProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DemoState>('NORMAL');
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  
  const [machines, setMachines] = useState<Machine[]>([]);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [rootCause, setRootCause] = useState<RootCause | null>(null);
  const [impact, setImpact] = useState<OperationalImpact | null>(null);
  const [recoveryActions, setRecoveryActions] = useState<RecoveryAction[]>([]);
  const [workflowActivity, setWorkflowActivity] = useState<WorkflowAction[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'CONNECTING' | 'CONNECTED' | 'OFFLINE'>('CONNECTING');

  useEffect(() => {
    let isMounted = true;
    
    const fetchState = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/state`);
        if (!response.ok) throw new Error('API error');
        const data = await response.json();
        
        if (isMounted) {
          setState(data.demoState as DemoState);
          setMachines(data.machines);
          setIncident(data.incident);
          setRootCause(data.rootCause);
          setImpact(data.impact);
          setRecoveryActions(data.recoveryActions || []);
          setWorkflowActivity(data.workflowActivity || []);
          setConnectionStatus('CONNECTED');
        }
      } catch (error) {
        if (isMounted) {
          setConnectionStatus('OFFLINE');
        }
      }
    };

    fetchState();
    const intervalId = setInterval(fetchState, 1000);
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const executeRecoveryAction = async (actionId: string) => {
    setSelectedActionId(actionId);
    try {
        const targetMachine = incident?.affectedMachineId || 'M03';
        const cleanActionId = actionId.replace(/^ACT-/, '');
        const response = await fetch(`${API_BASE_URL}/api/recovery/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ machine_id: targetMachine, action_id: cleanActionId })
        });
        
        if (!response.ok) {
            console.error('Failed to execute recovery action, status:', response.status);
        } else {
            const data = await response.json();
            if (data.execution_status === 'INVALID_ACTION') {
                console.error('Backend rejected action:', data.message);
            }
        }
    } catch (e) {
        console.error('Failed to execute recovery action:', e);
    }
  };

  const injectFault = async (machineId: string, faultType: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/fault/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ machine_id: machineId, fault_type: faultType, severity: 'critical' })
      });

      const res = await fetch(`${API_BASE_URL}/api/state`);
      if (!res.ok) throw new Error('Failed to fetch state after fault injection');
      const data = await res.json();
      
      const targetMachine = data.machines.find((m: any) => m.id === machineId);
      if (targetMachine) {
        const payload = {
          machine_id: machineId,
          telemetry: {
            temperature: targetMachine.telemetry.temperature,
            vibration: targetMachine.telemetry.vibration,
            throughput: targetMachine.telemetry.throughput,
            power_consumption: targetMachine.telemetry.power_consumption,
            defect_rate: targetMachine.telemetry.defect_rate
          }
        };

        const webhookUrl = import.meta.env.VITE_N8N_WEBHOOK_URL;
        if (webhookUrl) {
          await fetch(webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          console.log('Telemetry sent to n8n Webhook');
        } else {
          console.warn('VITE_N8N_WEBHOOK_URL is not defined in frontend env.');
        }
      }
    } catch (e) {
      console.error('Failed to inject fault:', e);
    }
  };

  const resetFactory = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/fault/reset`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to reset factory:', e);
    }
  };

  return (
    <DemoContext.Provider value={{ 
        state, 
        setState, 
        selectedActionId, 
        executeRecoveryAction,
        injectFault,
        resetFactory,
        machines,
        incident,
        rootCause,
        impact,
        recoveryActions,
        workflowActivity,
        connectionStatus
    }}>
      {children}
    </DemoContext.Provider>
  );
}

export const useDemoState = () => {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemoState must be used within a DemoProvider');
  }
  return context;
};
