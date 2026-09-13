import { useState } from 'react';
import { useDemoState } from '../../hooks/useDemoState';
import { Badge } from '../../components/common/Badge';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { ArrowDown, X, AlertTriangle } from 'lucide-react';
import styles from './LiveProduction.module.css';

// Helper to generate simple stable or dropping mock trend data based on state
const generateTrendData = (baseValue: number, isAnomaly: boolean, type: 'up' | 'down') => {
  return Array.from({ length: 20 }).map((_, i) => {
    let val = baseValue + (Math.random() * (baseValue * 0.05) - (baseValue * 0.025)); // +/- 2.5% noise
    if (isAnomaly && i > 10) {
      const factor = type === 'up' ? 1 + (i - 10) * 0.05 : 1 - (i - 10) * 0.05;
      val = val * factor;
    }
    return { time: `${i}m`, value: val };
  });
};

export default function LiveProduction() {
  const { state, machines, rootCause } = useDemoState();
  const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null);

  const selectedMachine = machines.find(m => m.id === selectedMachineId);
  const isSelectedMachineCritical = selectedMachine?.state === 'CRITICAL' || selectedMachine?.state === 'WARNING';

  return (
    <div className={styles.container}>
      {/* Main Left Area: Topology */}
      <div className={`${styles.topologyArea} ${selectedMachineId ? styles.drawerOpen : ''}`}>
        <div className={styles.header}>
          <h2>Live Production Telemetry</h2>
          <p className={styles.subtitle}>Click any machine node to view detailed diagnostics.</p>
        </div>

        <div className={styles.topologyFlow}>
          <div className={styles.externalNode}>RAW MATERIAL</div>
          <div className={styles.flowArrow}><ArrowDown size={24} /></div>

          {machines.map((machine, index) => (
            <div key={`vert-${machine.id}`} className={styles.vertNodeWrapper}>
              <div 
                className={`${styles.vertNode} ${styles[`vert_${machine.state.toLowerCase()}`]} ${selectedMachineId === machine.id ? styles.selectedNode : ''}`}
                onClick={() => setSelectedMachineId(machine.id)}
              >
                <div className={styles.nodeIdentity}>
                  <span className={styles.nodeId}>{machine.id}</span>
                  <span className={styles.nodeName}>{machine.name}</span>
                </div>
                
                <div className={styles.nodeStats}>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Throughput</span>
                    <span className={styles.statValue}>{machine.telemetry.throughput.toLocaleString()} u/h</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Temperature</span>
                    <span className={styles.statValue}>{machine.telemetry.temperature}°C</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Vibration</span>
                    <span className={styles.statValue}>{machine.telemetry.vibration} mm/s</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Cycle</span>
                    <span className={styles.statValue}>{machine.telemetry.cycleTime}s</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Quality</span>
                    <span className={styles.statValue}>{machine.telemetry.quality}%</span>
                  </div>
                  <Badge variant={machine.state.toLowerCase() as any} size="sm" className={styles.nodeBadge}>
                    {machine.state}
                  </Badge>
                </div>
              </div>
              
              {index < machines.length - 1 && (
                <div className={`${styles.flowArrow} ${machine.state === 'CRITICAL' ? styles.flowArrowCritical : ''}`}>
                  <ArrowDown size={24} />
                </div>
              )}
            </div>
          ))}

          <div className={styles.flowArrow}><ArrowDown size={24} /></div>
          <div className={styles.externalNode}>PACKAGING</div>
        </div>
      </div>

      {/* Right Drawer: Machine Details */}
      {selectedMachine && (
        <div className={styles.rightDrawer}>
          <div className={styles.drawerHeader}>
            <div className={styles.drawerTitle}>
              <span className={styles.drawerMachineId}>{selectedMachine.id}</span>
              <span className={styles.drawerMachineName}>{selectedMachine.name}</span>
            </div>
            <button className={styles.closeBtn} onClick={() => setSelectedMachineId(null)}>
              <X size={24} />
            </button>
          </div>

          <div className={styles.drawerContent}>
            <div className={styles.drawerStatusRow}>
              <span>STATUS</span>
              <Badge variant={selectedMachine.state.toLowerCase() as any} pulsing={isSelectedMachineCritical}>
                {selectedMachine.state}
              </Badge>
            </div>

            {isSelectedMachineCritical && state !== 'RECOVERY_COMPLETE' && (
              <div className={styles.whyCriticalBlock}>
                <div className={styles.whyHeader}>
                  <AlertTriangle size={16} />
                  <span>AI SIGNALS</span>
                </div>
                <ul className={styles.whyList}>
                  {rootCause?.evidence?.map((ev, i) => (
                    <li key={i}>{ev.metric} {ev.trend === 'UP' ? 'anomaly' : 'deviation'}</li>
                  ))}
                </ul>

                <div className={styles.causeSection}>
                  <div className={styles.whyHeader}>
                    <span>PROBABLE CAUSE</span>
                  </div>
                  <p className={styles.causeDesc}>{rootCause?.description}</p>
                  <p className={styles.causeConf}>{rootCause?.confidence}% confidence</p>
                </div>

                <button 
                  className={styles.viewIncidentBtn}
                  onClick={() => window.location.href = '/incident'}
                >
                  VIEW INCIDENT ANALYSIS
                </button>
              </div>
            )}

            <div className={styles.telemetryGrid}>
              {/* Throughput */}
              <div className={styles.tCard}>
                <div className={styles.tCardHeader}>Throughput</div>
                <div className={`${styles.tCardValue} ${isSelectedMachineCritical ? styles.textRed : ''}`}>
                  {selectedMachine.telemetry.throughput.toLocaleString()} <small>u/h</small>
                </div>
                <div className={styles.tCardChart}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={generateTrendData(selectedMachine.telemetry.throughput, isSelectedMachineCritical, 'down')}>
                      <Line type="monotone" dataKey="value" stroke={isSelectedMachineCritical ? "var(--violet-bright)" : "var(--green)"} strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Temperature */}
              <div className={styles.tCard}>
                <div className={styles.tCardHeader}>Temperature</div>
                <div className={`${styles.tCardValue} ${isSelectedMachineCritical ? styles.textRed : ''}`}>
                  {selectedMachine.telemetry.temperature}°C
                </div>
                <div className={styles.tCardChart}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={generateTrendData(selectedMachine.telemetry.temperature, isSelectedMachineCritical, 'up')}>
                      <Line type="monotone" dataKey="value" stroke={isSelectedMachineCritical ? "var(--violet-bright)" : "var(--green)"} strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Vibration */}
              <div className={styles.tCard}>
                <div className={styles.tCardHeader}>Vibration</div>
                <div className={`${styles.tCardValue} ${isSelectedMachineCritical ? styles.textRed : ''}`}>
                  {selectedMachine.telemetry.vibration} <small>mm/s</small>
                </div>
                <div className={styles.tCardChart}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={generateTrendData(selectedMachine.telemetry.vibration, isSelectedMachineCritical, 'up')}>
                      <Line type="monotone" dataKey="value" stroke={isSelectedMachineCritical ? "var(--violet-bright)" : "var(--green)"} strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
