import { useDemoState } from '../../hooks/useDemoState';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { AlertTriangle, TrendingUp, TrendingDown, ServerCrash, CheckCircle, Search, GitPullRequest, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './IncidentAnalysis.module.css';

export default function IncidentAnalysis() {
  const { incident, rootCause, impact, recoveryActions } = useDemoState();
  const navigate = useNavigate();


  if (!incident || incident.status !== 'ACTIVE') {
    return (
      <div className={styles.emptyState}>
        <CheckCircle size={48} className={styles.iconSuccess} />
        <h2>No Active Incidents</h2>
        <p>System is operating within normal parameters. AI analysis is currently on standby.</p>
      </div>
    );
  }

  const getEvidenceIcon = (trend: string) => {
    switch (trend) {
      case 'UP': return <TrendingUp size={16} className={styles.textRed} />;
      case 'DOWN': return <TrendingDown size={16} className={styles.textRed} />;
      case 'CRASH': return <ServerCrash size={16} className={styles.textRed} />;
      default: return <AlertTriangle size={16} className={styles.textAmber} />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch(severity) {
      case 'HIGH': return <Badge variant="critical">HIGH</Badge>;
      case 'MEDIUM': return <Badge variant="warning">MEDIUM</Badge>;
      default: return <Badge variant="neutral">{severity}</Badge>;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Incident Intelligence</h2>
        <p className={styles.subtitle}>AI-driven root cause analysis and impact estimation.</p>
      </div>

      <div className={styles.chainContainer}>
        <div className={styles.chainLine}></div>

        {/* Step 1: Anomaly Detected */}
        <div className={styles.chainStep}>
          <div className={styles.stepNode}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabel}>1. ANOMALY DETECTED</div>
            <div className={styles.incidentHeader}>
              <Search size={24} className={styles.iconBlue} />
              <div className={styles.incidentTitleBlock}>
                <h3>{incident.title}</h3>
                <span className={styles.machineRef}>Source: {incident.affectedMachineId}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Step 2: Evidence */}
        <div className={styles.chainStep}>
          <div className={styles.stepNode}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabel}>2. EVIDENCE</div>
            <div className={styles.evidenceList}>
              {rootCause?.evidence?.map((ev, i) => (
                <div key={i} className={styles.evidenceItem}>
                  {getEvidenceIcon(ev.trend)}
                  <span className={styles.evMetric}>{ev.metric}</span>
                  <strong className={styles.evChange}>{ev.change}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Step 3: Probable Root Cause */}
        <div className={styles.chainStep}>
          <div className={styles.stepNodeAi}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabelAi}>3. PROBABLE ROOT CAUSE</div>
            <div className={styles.causeBlock}>
              <div className={styles.causeHeader}>
                <GitPullRequest size={24} />
                <h3>{rootCause?.description}</h3>
              </div>
            </div>
          </div>
        </div>

        {/* Step 4: Confidence */}
        <div className={styles.chainStep}>
          <div className={styles.stepNodeAi}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabelAi}>4. CONFIDENCE</div>
            <div className={styles.confidenceBadge}>
              <strong>{rootCause?.confidence}%</strong>
              <span>Correlation matched against historical fault profiles and operating procedures.</span>
            </div>
          </div>
        </div>

        {/* Step 5: Operational Impact */}
        <div className={styles.chainStep}>
          <div className={styles.stepNode}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabel}>5. OPERATIONAL IMPACT</div>
            <div className={styles.impactGrid}>
              <div className={styles.impactItem}>
                <span className={styles.impactLabel}>Production Loss</span>
                <span className={styles.impactValueBad}>{impact?.productionLossPercentage}%</span>
              </div>
              <div className={styles.impactItem}>
                <span className={styles.impactLabel}>Est. Downtime</span>
                <span className={styles.impactValueBad}>{impact?.estimatedDowntimeMinutes}m</span>
              </div>
              <div className={styles.impactItem}>
                <span className={styles.impactLabel}>Quality Risk</span>
                {getSeverityBadge(impact?.qualityRisk || 'LOW')}
              </div>
              <div className={styles.impactItem}>
                <span className={styles.impactLabel}>Affected Orders</span>
                <span className={styles.impactValue}>{impact?.affectedOrders}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Step 6: Recommendation */}
        <div className={styles.chainStep}>
          <div className={styles.stepNodeAi}></div>
          <div className={styles.stepContent}>
            <div className={styles.stepLabelAi}>6. CAUSEN RECOMMENDATION</div>
            <div className={styles.recommendationBlock}>
              <div className={styles.recHeader}>
                <Activity size={24} color="var(--violet-bright)" />
                <h3 style={{color: 'var(--violet-bright)'}}>{recoveryActions?.[0]?.title}</h3>
              </div>
              <div className={styles.recFooter}>
                <Button size="lg" variant="primary" onClick={() => navigate('/simulator')}>
                  Evaluate Recovery Options
                </Button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
