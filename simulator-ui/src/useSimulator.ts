import { useState, useEffect } from 'react';
import { API_BASE_URL } from './config';

export type MachineState = 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'RECOVERING' | 'RECOVERED/HEALTHY';

export interface Telemetry {
  throughput: number;
  cycleTime: number;
  temperature: number;
  vibration: number;
  quality: number;
}

export interface Machine {
  id: string;
  name: string;
  state: MachineState;
  telemetry: Telemetry;
}

export interface SimulatorState {
  demoState: string;
  machines: Machine[];
  incident?: any;
  rootCause?: any;
  impact?: any;
  recoveryActions?: any[];
  workflowActivity?: any[];
  pending_approval?: any;
}

export const useSimulator = () => {
  const [state, setState] = useState<SimulatorState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [webhookError, setWebhookError] = useState<string | null>(null);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/state`);
        if (!res.ok) throw new Error('Failed to fetch state');
        const data = await res.json();
        setState(data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      }
    };

    fetchState();
    const interval = setInterval(fetchState, 1000);
    return () => clearInterval(interval);
  }, []);

  const injectFault = async (machineId: string, faultType: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/fault/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ machine_id: machineId, fault_type: faultType, severity: 'critical' })
      });

      // Fetch latest state immediately to capture the injected fault telemetry
      const res = await fetch(`${API_BASE_URL}/api/state`);
      if (!res.ok) throw new Error('Failed to fetch state after fault injection');
      const data = await res.json();
      setState(data);
      
      // Find the affected machine telemetry
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
          try {
            await fetch(webhookUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });
            console.log('Telemetry sent to n8n Webhook');
            setWebhookError(null);
          } catch (webhookErr: any) {
            console.error('Failed to send telemetry to n8n Webhook', webhookErr);
            setWebhookError(`Failed to connect to n8n Webhook at ${webhookUrl}`);
          }
        } else {
          console.warn('VITE_N8N_WEBHOOK_URL is not defined.');
        }
      }

    } catch (e: any) {
      console.error('Failed to inject fault', e);
      setError(e.message);
    }
  };

  const resetFactory = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/fault/reset`, { method: 'POST' });
      setWebhookError(null);
    } catch (e) {
      console.error('Failed to reset factory', e);
    }
  };

  const resolveApproval = async (machineId: string, action: 'approved' | 'rejected') => {
    try {
      await fetch(`${API_BASE_URL}/api/approval/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ machine_id: machineId, action })
      });
      // State polling will pick up the cleared approval automatically
    } catch (e: any) {
      console.error('Failed to resolve approval', e);
      setError(e.message);
    }
  };

  return { state, error, webhookError, injectFault, resetFactory, resolveApproval };
};
