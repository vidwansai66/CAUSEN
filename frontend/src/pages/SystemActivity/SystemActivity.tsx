import { useDemoState } from '../../hooks/useDemoState';
import { Card } from '../../components/common/Card';
import { Info, AlertTriangle, XOctagon, CheckCircle2 } from 'lucide-react';
import styles from './SystemActivity.module.css';

export default function SystemActivity() {
  const { state, workflowActivity, incident, rootCause } = useDemoState();
  
  let activities: {id: string, timestamp: string, type: string, message: string}[] = [];

  if (state === 'NORMAL') {
    activities = [
      { id: '1', timestamp: '08:00:00', type: 'INFO', message: 'System initialization complete.' },
      { id: '2', timestamp: '09:15:30', type: 'INFO', message: 'Routine diagnostic passed on M05.' }
    ];
  } else if (state === 'WARNING') {
    activities = [
      { id: '1', timestamp: '10:41:00', type: 'WARNING', message: 'Vibration increase detected on M03.' }
    ];
  } else if (state === 'CRITICAL' || state === 'RECOVERY' || state === 'RECOVERY_COMPLETE') {
    const machineId = incident?.affectedMachineId || 'Unknown Machine';
    const causeDesc = rootCause?.description || 'Unknown Cause';
    
    activities = [
      { id: '1', timestamp: '10:41:12', type: 'CRITICAL', message: `Anomaly detected — ${machineId}` },
      { id: '2', timestamp: '10:41:18', type: 'CRITICAL', message: 'Incident classified — CRITICAL' },
      { id: '3', timestamp: '10:41:22', type: 'INFO', message: 'Evidence correlation completed' },
      { id: '4', timestamp: '10:41:25', type: 'WARNING', message: `Root cause identified — ${causeDesc}` },
      { id: '5', timestamp: '10:41:27', type: 'INFO', message: 'Recovery simulations generated' }
    ];
    
    if (state === 'RECOVERY' || state === 'RECOVERY_COMPLETE') {
    if (workflowActivity && workflowActivity.length > 0) {
      workflowActivity.forEach((w, i) => {
        activities.push({
          id: `w-${i}`,
          timestamp: w.timestamp,
          type: 'INFO',
          message: w.name
        });
      });
    }
    if (state === 'RECOVERY_COMPLETE') {
      activities.push({
        id: 'r-done', timestamp: 'Just now', type: 'SUCCESS', message: 'Recovery completed successfully.'
      });
    }
    }
  }

  const getEventIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'INFO': return <Info size={16} className={styles.iconInfo} />;
      case 'WARNING': return <AlertTriangle size={16} className={styles.iconWarning} />;
      case 'CRITICAL': 
      case 'ERROR': return <XOctagon size={16} className={styles.iconError} />;
      case 'SUCCESS': return <CheckCircle2 size={16} className={styles.iconSuccess} />;
      default: return <Info size={16} />;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>System Activity Log</h2>
        <p className={styles.subtitle}>Audit trail of system events, detections, and automated actions.</p>
      </div>

      <Card className={styles.timelineCard}>
        <div className={styles.timeline}>
          {[...activities].reverse().map((event, index) => (
            <div key={event.id} className={styles.timelineItem}>
              <div className={styles.timeColumn}>
                {event.timestamp}
              </div>
              <div className={styles.nodeColumn}>
                <div className={`${styles.node} ${styles[event.type.toLowerCase()]}`}>
                  {getEventIcon(event.type)}
                </div>
                {index !== activities.length - 1 && <div className={styles.line}></div>}
              </div>
              <div className={styles.contentColumn}>
                <div className={styles.message}>{event.message}</div>
                <div className={styles.eventId}>Event ID: {event.id}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
