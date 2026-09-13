import { useDemoState } from '../../hooks/useDemoState';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { ArrowRight, Play, ChevronRight, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './Overview.module.css';

export default function Overview() {
  const { state, executeRecoveryAction, machines, incident, rootCause, impact, recoveryActions } = useDemoState();
  const navigate = useNavigate();
  
  const recommendedAction = recoveryActions?.find(a => a.type === 'REROUTE') || recoveryActions?.[0];

  const totalThroughput = machines.reduce((acc, m) => acc + m.telemetry.throughput, 0);
  const avgQuality = machines.reduce((acc, m) => acc + m.telemetry.quality, 0) / machines.length;

  if (state === 'NORMAL' || !incident) {
    return (
      <div className={styles.container}>
        <div className={styles.healthyState}>
          <Activity size={48} className={styles.iconSuccess} />
          <h2 className={styles.healthyTitle}>SYSTEM HEALTHY</h2>
          <div className={styles.healthyMetrics}>
            <div className={styles.hMetric}>
              <span>Line Throughput</span>
              <strong>{totalThroughput.toLocaleString()} u/h</strong>
            </div>
            <div className={styles.hMetric}>
              <span>Line Quality Yield</span>
              <strong>{avgQuality.toFixed(1)}%</strong>
            </div>
            <div className={styles.hMetric}>
              <span>Downtime Risk</span>
              <strong className={styles.textGreen}>LOW</strong>
            </div>
          </div>
          <Button variant="secondary" onClick={() => navigate('/live')}>View Live Telemetry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.layoutGrid}>
        
        {/* Left Column: Core Incident & Impact */}
        <div className={styles.leftCol}>
          <div className={styles.incidentHero}>
            <div className={styles.incidentTag}>
              <Badge variant={state === 'CRITICAL' ? 'critical' : state === 'RECOVERY' ? 'info' : 'warning'} pulsing>
                {state === 'CRITICAL' ? 'CRITICAL INCIDENT' : state === 'RECOVERY' ? 'RECOVERY IN PROGRESS' : 'WARNING DETECTED'}
              </Badge>
              <span className={styles.machineId}>{incident.affectedMachineId}</span>
            </div>
            <h1 className={styles.incidentTitle}>
              {incident.title}
            </h1>
          </div>

          <div className={styles.telemetryBlock}>
            <div className={styles.blockLabel}>ANOMALY DETECTED</div>
            <div className={styles.telemetryItems}>
              {rootCause?.evidence.map((ev, i) => (
                <span key={i} className={styles.anomalyItem}>
                  {ev.metric} <span className={ev.trend === 'UP' ? styles.arrowUp : styles.arrowDown}>
                    {ev.trend === 'UP' ? '↑' : '↓'}
                  </span>
                </span>
              ))}
            </div>
          </div>

          <div className={styles.causeBlock}>
            <div className={styles.blockLabel}>PROBABLE CAUSE</div>
            <div className={styles.causeContent}>
              <h3 className={styles.causeTitle}>{rootCause?.description}</h3>
              <div className={styles.confidenceScore}>
                <strong>{rootCause?.confidence}%</strong> confidence
              </div>
            </div>
          </div>

          <div className={styles.impactGrid}>
            <div className={styles.impactBox}>
              <span className={styles.impactLabel}>PRODUCTION LOSS</span>
              <span className={styles.impactValueBad}>{impact?.productionLossPercentage}%</span>
            </div>
            <div className={styles.impactBox}>
              <span className={styles.impactLabel}>EST. DOWNTIME</span>
              <span className={styles.impactValueBad}>{impact?.estimatedDowntimeMinutes}m</span>
            </div>
            <div className={styles.impactBox}>
              <span className={styles.impactLabel}>AFFECTED ORDERS</span>
              <span className={styles.impactValue}>{impact?.affectedOrders}</span>
            </div>
          </div>

          <Button 
            variant="secondary" 
            className={styles.analyzeBtn}
            onClick={() => navigate('/incident')}
          >
            View Full Analysis <ChevronRight size={16} />
          </Button>
        </div>

        {/* Right Column: Recommendation & Topology */}
        <div className={styles.rightCol}>
          
          {recommendedAction && (
          <Card className={styles.recommendationPanel}>
            <div className={styles.recHeader}>
              <Badge variant="ai" className={styles.recLabel}>CAUSEN RECOMMENDS</Badge>
              <div className={styles.recConfidence}><strong>{recommendedAction.confidence}%</strong> CONFIDENCE</div>
            </div>
            
            <h2 className={styles.recTitle}>{recommendedAction.title}</h2>
            <p className={styles.recRationale}>
              {recommendedAction.rationale}
            </p>

            <div className={styles.recMetrics}>
              <div className={styles.rMetric}>
                <span>Expected Prod. Loss</span>
                <strong>{recommendedAction.expectedProductionLoss}%</strong>
              </div>
              <div className={styles.rMetric}>
                <span>Recovery Time</span>
                <strong>{recommendedAction.expectedDowntime} min</strong>
              </div>
            </div>

            <div className={styles.recActions}>
              <Button variant="secondary" onClick={() => navigate('/simulator')}>Compare Options</Button>
              <Button 
                variant="primary" 
                icon={<Play size={16} />}
                onClick={() => {
                  executeRecoveryAction(recommendedAction.id);
                  navigate('/actions');
                }}
              >
                Execute
              </Button>
            </div>
          </Card>
          )}

          <Card className={styles.topologyPanel}>
            <div className={styles.panelHeader}>
              <span className={styles.panelTitle}>PRODUCTION LINE TOPOLOGY</span>
              <Button variant="secondary" size="sm" onClick={() => navigate('/live')}>View Telemetry</Button>
            </div>
            <div className={styles.topologyLine}>
              {machines.map((machine, index) => (
                <div key={machine.id} className={styles.topologyNodeWrapper}>
                  <div className={`${styles.topologyNode} ${styles[`top_${machine.state.toLowerCase()}`]}`}>
                    {machine.id}
                  </div>
                  {index < machines.length - 1 && (
                    <div className={styles.topologyArrow}>
                      <ArrowRight size={16} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>

        </div>
      </div>
    </div>
  );
}
