import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

export interface MachineTelemetry {
  throughput: number;
  temperature: number;
  vibration: number;
  cycleTime: number;
  quality: number;
}

export interface Machine {
  id: string;
  name: string;
  state: 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'RECOVERING';
  telemetry: MachineTelemetry;
}

export interface SimulatorState {
  demoState: string;
  machines: Machine[];
  connectionStatus: 'CONNECTING' | 'CONNECTED' | 'OFFLINE';
}

export function useSimulator() {
  const [state, setState] = useState<SimulatorState>({
    demoState: 'NORMAL',
    machines: [],
    connectionStatus: 'CONNECTING'
  });

  useEffect(() => {
    let isMounted = true;
    
    const fetchState = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/state`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        if (isMounted) {
          setState({
            demoState: data.demoState,
            machines: data.machines || [],
            connectionStatus: 'CONNECTED'
          });
        }
      } catch (error) {
        if (isMounted) {
          setState(prev => ({ ...prev, connectionStatus: 'OFFLINE' }));
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

  const injectFault = async (machineId: string, faultType: string, severity: string = 'critical') => {
    try {
        await fetch(`${API_BASE_URL}/api/fault/inject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              machine_id: machineId,
              fault_type: faultType,
              severity: severity
            })
        });
    } catch (e) {
        console.error('Failed to inject fault:', e);
    }
  };

  const resetSimulation = async () => {
    try {
        await fetch(`${API_BASE_URL}/api/fault/reset`, {
            method: 'POST'
        });
    } catch (e) {
        console.error('Failed to reset simulation:', e);
    }
  };

  return { ...state, injectFault, resetSimulation };
}
