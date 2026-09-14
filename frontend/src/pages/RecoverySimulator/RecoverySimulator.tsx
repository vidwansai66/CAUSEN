import { useState } from 'react';
import { useDemoState } from '../../hooks/useDemoState';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Play, ArrowRight, Settings, Activity, ShieldAlert, GitBranch, PauseCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './RecoverySimulator.module.css';

export default function RecoverySimulator() {
  const { incident, impact, recoveryActions, executeRecoveryAction, state, selectedActionId: executedActionId } = useDemoState();
  const navigate = useNavigate();
  
  const recommendedActionId = recoveryActions?.[0]?.id || '';
  const [selectedActionId, setSelectedActionId] = useState<string>(recommendedActionId);

  // If actions change, ensure selected is valid or update
  const selectedAction = recoveryActions?.find(a => a.id === selectedActionId) || recoveryActions?.[0];

  if (!incident || incident.status !== 'ACTIVE') {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2>Recovery Options Evaluation</h2>
            <p className={styles.subtitle}>Select an action to simulate expected outcomes.</p>
          </div>
        </div>

        <div className={styles.emptyState}>
          <Activity size={48} className={styles.icon} />
          <h2>No Active Incidents</h2>
          <p>The system is currently healthy and operating within normal parameters.</p>
        </div>
      </div>
    );
  }

  const handleExecute = () => {
    executeRecoveryAction(selectedActionId);
    navigate('/actions');
  };

  const getIconForType = (type: string) => {
    switch (type) {
      case 'REROUTE': return <GitBranch size={20} />;
      case 'STOP': return <PauseCircle size={20} />;
      case 'MAINTENANCE': return <Settings size={20} />;
      case 'SLOW': return <Activity size={20} />;
      default: return <ShieldAlert size={20} />;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h2>Recovery Options Evaluation</h2>
          <p className={styles.subtitle}>Select an action to simulate expected outcomes.</p>
        </div>
      </div>

      <div className={styles.layout}>
        {/* Left: Action Selection */}
        <div className={styles.optionsList}>
          {recoveryActions?.map((action) => (
            <div 
              key={action.id} 
              className={`${styles.actionItem} ${selectedActionId === action.id ? styles.selected : ''}`}
              onClick={() => setSelectedActionId(action.id)}
            >
              {action.id === recoveryActions?.[0]?.id && <Badge variant="ai" className={styles.recBadge}>RECOMMENDED</Badge>}
              <div className={styles.actionItemHeader}>
                <div className={styles.actionIcon}>{getIconForType(action.type)}</div>
                <div className={styles.actionTitleInfo}>
                  <h4>{action.title}</h4>
                  <span className={styles.actionType}>{action.type}</span>
                </div>
              </div>
              <p className={styles.actionDesc}>{action.description}</p>
            </div>
          ))}
        </div>

        {/* Right: Simulation Panel */}
        {selectedAction && (
        <Card className={styles.simulationPanel}>
          <div className={styles.simHeader}>
            <div className={styles.simTitle}>
              <Play size={20} color="var(--violet-bright)" />
              <h3>Simulation Results: {selectedAction.title}</h3>
            </div>
            <div className={styles.simConfidence}>
              <span>AI Confidence: <strong>{selectedAction.confidence}%</strong></span>
            </div>
          </div>

          <div className={styles.comparisonGrid}>
            <div className={styles.column}>
              <div className={styles.columnHeader}>CURRENT STATE <Badge variant="neutral" className={styles.dataBadge}>LIVE</Badge></div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Production Loss</span>
                <span className={styles.metricValueBad}>{impact?.productionLossPercentage}%</span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Downtime Risk</span>
                <span className={styles.metricValueBad}>HIGH</span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Affected Orders</span>
                <span className={styles.metricValue}>{impact?.affectedOrders}</span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Quality Risk</span>
                <span className={styles.metricValueBad}>{impact?.qualityRisk}</span>
              </div>
            </div>

            <div className={styles.vsColumn}>
              <ArrowRight size={24} color="var(--text-muted)" />
            </div>

            <div className={styles.column}>
              <div className={styles.columnHeaderAi}>PREDICTED AFTER <Badge variant="ai" className={styles.dataBadge}>SIMULATED</Badge></div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Production Loss</span>
                <span className={styles.metricValueGood}>{selectedAction.expectedProductionLoss}%</span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Est. Downtime</span>
                <span className={selectedAction.expectedDowntime > 0 ? styles.metricValueBad : styles.metricValueGood}>
                  {selectedAction.expectedDowntime} min
                </span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Affected Orders</span>
                <span className={styles.metricValueGood}>{selectedAction.affectedOrders}</span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Quality Risk</span>
                <span className={selectedAction.qualityRisk === 'LOW' ? styles.metricValueGood : styles.metricValueBad}>
                  {selectedAction.qualityRisk}
                </span>
              </div>
            </div>
          </div>

          <div className={styles.rationaleBox}>
            <span className={styles.rationaleLabel}>CAUSEN RATIONALE</span>
            <p>{selectedAction.rationale}</p>
          </div>

          <div className={styles.actionFooter}>
            <Button size="lg" variant="primary" onClick={handleExecute} disabled={state === 'RECOVERY' || !!executedActionId}>
              {state === 'RECOVERY' || executedActionId ? 'Executing Action...' : 'Execute Action'}
            </Button>
          </div>
        </Card>
        )}
      </div>
    </div>
  );
}
