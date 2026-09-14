import { useState } from 'react';
import type { Machine } from './useSimulator';
import { useSimulator } from './useSimulator';
import { VapiVoiceButton } from './VapiVoiceButton';
import { Sparkline } from './Sparkline';
import { Activity, AlertTriangle, CheckCircle, Flame, Server, RotateCcw, AlertOctagon, Check, X } from 'lucide-react';
import { API_BASE_URL } from './config';
import './App.css';

function App() {
  const { state, error, webhookError, injectFault, resetFactory, resolveApproval } = useSimulator();
  const [selectedMachine, setSelectedMachine] = useState<string>('M03');
  const [selectedFault, setSelectedFault] = useState<string>('DISRUPTION_01_COOLING_SYSTEM_DEGRADATION');

  const handleInject = () => {
    injectFault(selectedMachine, selectedFault);
  };

  if (error) {
    return (
      <div style={{ padding: '2rem', color: 'red', fontFamily: 'monospace' }}>
        <h2>Connection Error</h2>
        <p>Could not connect to Simulator Backend: {error}</p>
        <p>Ensure backend is running at {API_BASE_URL}</p>
      </div>
    );
  }

  if (!state) {
    return <div style={{ padding: '2rem', color: 'white', fontFamily: 'monospace' }}>Connecting to Factory Core...</div>;
  }

  const globalStatus = state.demoState || 'HEALTHY';
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY': return <CheckCircle size={24} />;
      case 'WARNING': return <AlertTriangle size={24} />;
      case 'CRITICAL': return <AlertOctagon size={24} />;
      case 'RECOVERING': return <Activity size={24} />;
      default: return <Server size={24} />;
    }
  };

  const getStatusClass = (status: string) => {
    return status.toLowerCase();
  };

  return (
    <div className="simulator-container">
      <header className="header">
        <div className="header-title">
          <Server size={28} />
          FACTORY CONTROL ROOM
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className={`status-badge ${getStatusClass(globalStatus)}`}>
            SYS_STATE: {globalStatus}
          </div>
        </div>
      </header>

      <div className="main-content">
        {webhookError && (
          <div style={{ backgroundColor: '#4a1111', color: '#ffaaaa', padding: '1rem', marginBottom: '1rem', borderRadius: '4px', border: '1px solid #ff0000' }}>
            <AlertTriangle size={18} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
            {webhookError}
          </div>
        )}

        {state.pending_approval && (
          <div className="approval-panel" style={{ backgroundColor: '#1a0505', border: '2px solid #ff0000', padding: '1.5rem', marginBottom: '2rem', borderRadius: '8px', boxShadow: '0 0 20px rgba(255, 0, 0, 0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
              <AlertOctagon size={28} color="#ff3333" style={{ marginRight: '1rem' }} />
              <h2 style={{ margin: 0, color: '#ff3333', fontSize: '1.5rem', letterSpacing: '1px' }}>CRITICAL RECOVERY APPROVAL REQUIRED</h2>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ backgroundColor: '#000', padding: '1rem', borderRadius: '4px', border: '1px solid #333' }}>
                <div style={{ color: '#888', fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Target Machine</div>
                <div style={{ color: '#fff', fontSize: '1.2rem', fontWeight: 'bold' }}>{state.pending_approval.machine_id}</div>
              </div>
              <div style={{ backgroundColor: '#000', padding: '1rem', borderRadius: '4px', border: '1px solid #333' }}>
                <div style={{ color: '#888', fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Recommended Action</div>
                <div style={{ color: '#ffaa00', fontSize: '1.2rem', fontWeight: 'bold' }}>{state.pending_approval.recommended_action}</div>
              </div>
            </div>

            <div style={{ backgroundColor: '#000', padding: '1rem', borderRadius: '4px', border: '1px solid #333', marginBottom: '1.5rem' }}>
              <div style={{ color: '#888', fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase' }}>AI Reasoning (Confidence: {state.pending_approval.confidence})</div>
              <div style={{ color: '#ddd', fontSize: '1rem', lineHeight: '1.4' }}>{state.pending_approval.reason}</div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                onClick={() => resolveApproval(state.pending_approval.machine_id, 'approved')}
                style={{ flex: 1, padding: '1rem', backgroundColor: '#33aa33', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <Check size={20} />
                APPROVE STOP
              </button>
              <button 
                onClick={() => resolveApproval(state.pending_approval.machine_id, 'rejected')}
                style={{ flex: 1, padding: '1rem', backgroundColor: '#444', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <X size={20} />
                REJECT
              </button>
            </div>
          </div>
        )}
        <div className="control-panel">
          <div className="control-group">
            <label>Target Machine</label>
            <select 
              className="control-select"
              value={selectedMachine}
              onChange={(e) => setSelectedMachine(e.target.value)}
            >
              {state.machines.map(m => (
                <option key={m.id} value={m.id}>{m.id} - {m.name}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Fault Profile</label>
            <select 
              className="control-select"
              value={selectedFault}
              onChange={(e) => setSelectedFault(e.target.value)}
            >
              <option value="DISRUPTION_01_COOLING_SYSTEM_DEGRADATION">Cooling System Degradation</option>
              <option value="DISRUPTION_02_BEARING_DEGRADATION">Spindle Bearing Wear</option>
              <option value="DISRUPTION_03_THROUGHPUT_DEGRADATION">Throughput Degradation</option>
            </select>
          </div>

          <div style={{ flex: 1 }}></div>

          <div className="control-group">
            <button className="btn btn-inject" onClick={handleInject} disabled={globalStatus === 'CRITICAL' || globalStatus === 'RECOVERING'}>
              <Flame size={18} />
              Inject Fault
            </button>
            <button className="btn btn-reset" onClick={resetFactory}>
              <RotateCcw size={18} />
              Reset Factory
            </button>
          </div>
        </div>

        <div className="machine-grid-container">
          <div className="machine-grid">
            {state.machines.map((m: Machine) => (
              <div key={m.id} className={`machine-card ${getStatusClass(m.state)}`}>
                <div className="machine-header">
                  <div>
                    <div className="machine-id">{m.id}</div>
                    <div className="machine-name">{m.name}</div>
                  </div>
                  <div className={`machine-status-icon ${getStatusClass(m.state)}`}>
                    {getStatusIcon(m.state)}
                  </div>
                </div>

                <div className="telemetry-grid">
                  <div className="telemetry-item">
                    <span className="telemetry-label">Throughput</span>
                    <span className="telemetry-value">
                      <span style={{ color: (m.safe_limits && m.telemetry.throughput <= m.safe_limits.throughput_min) ? '#f87171' : 'inherit' }}>{m.telemetry.throughput.toFixed(0)} UPH</span>
                      {m.safe_limits && <span style={{ fontSize: '0.65em', color: '#9ca3af', marginLeft: '6px' }}>(MIN: {m.safe_limits.throughput_min})</span>}
                    </span>
                    {m.history && (
                      <div style={{ marginTop: '4px' }}>
                        <Sparkline data={m.history.throughput} color={(m.safe_limits && m.telemetry.throughput <= m.safe_limits.throughput_min) ? '#f87171' : '#34d399'} />
                      </div>
                    )}
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label">Temperature</span>
                    <span className="telemetry-value">
                      <span style={{ color: (m.safe_limits && m.telemetry.temperature >= m.safe_limits.temperature_max) ? '#f87171' : 'inherit' }}>{m.telemetry.temperature.toFixed(1)} °C</span>
                      {m.safe_limits && <span style={{ fontSize: '0.65em', color: '#9ca3af', marginLeft: '6px' }}>(MAX: {m.safe_limits.temperature_max})</span>}
                    </span>
                    {m.history && (
                      <div style={{ marginTop: '4px' }}>
                        <Sparkline data={m.history.temperature} color={(m.safe_limits && m.telemetry.temperature >= m.safe_limits.temperature_max) ? '#f87171' : '#34d399'} />
                      </div>
                    )}
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label">Vibration</span>
                    <span className="telemetry-value">
                      <span style={{ color: (m.safe_limits && m.telemetry.vibration >= m.safe_limits.vibration_max) ? '#f87171' : 'inherit' }}>{m.telemetry.vibration.toFixed(2)} mm/s</span>
                      {m.safe_limits && <span style={{ fontSize: '0.65em', color: '#9ca3af', marginLeft: '6px' }}>(MAX: {m.safe_limits.vibration_max})</span>}
                    </span>
                    {m.history && (
                      <div style={{ marginTop: '4px' }}>
                        <Sparkline data={m.history.vibration} color={(m.safe_limits && m.telemetry.vibration >= m.safe_limits.vibration_max) ? '#f87171' : '#34d399'} />
                      </div>
                    )}
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label">Quality</span>
                    <span className="telemetry-value">{m.telemetry.quality.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
