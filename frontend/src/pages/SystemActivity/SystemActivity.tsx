import { useMemo } from 'react';
import { useDemoState } from '../../hooks/useDemoState';
import { Card } from '../../components/common/Card';
import { Info, AlertTriangle, XOctagon, CheckCircle2 } from 'lucide-react';
import styles from './SystemActivity.module.css';

export default function SystemActivity() {
  const { state, workflowActivity, incident, rootCause } = useDemoState();
  
  const activities = useMemo(() => {
    let acts: {id: string, timestamp: string, type: string, message: string}[] = [];

    const now = new Date();
    const formatTime = (date: Date) => date.toLocaleTimeString('en-US', { hour12: false });
    const timeMinusSecs = (seconds: number) => formatTime(new Date(now.getTime() - seconds * 1000));
    const timeMinusMins = (minutes: number) => formatTime(new Date(now.getTime() - minutes * 60000));

    if (state === 'NORMAL') {
      acts = [
        { id: '1', timestamp: timeMinusMins(120), type: 'INFO', message: 'System initialization complete.' },
        { id: '2', timestamp: timeMinusMins(45), type: 'INFO', message: 'Routine diagnostic passed on M05.' }
      ];
    } else if (state === 'WARNING') {
      acts = [
        { id: '1', timestamp: timeMinusSecs(30), type: 'WARNING', message: 'Vibration increase detected on M03.' }
      ];
    } else if (state === 'CRITICAL' || state === 'RECOVERY' || state === 'RECOVERY_COMPLETE') {
      const machineId = incident?.affectedMachineId || 'Unknown Machine';
      const causeDesc = rootCause?.description || 'Unknown Cause';
      
      // In demo, we pretend the incident started 2 minutes ago
      acts = [
        { id: '1', timestamp: timeMinusSecs(120), type: 'CRITICAL', message: `Anomaly detected — ${machineId}` },
        { id: '2', timestamp: timeMinusSecs(115), type: 'CRITICAL', message: 'Incident classified — CRITICAL' },
        { id: '3', timestamp: timeMinusSecs(110), type: 'INFO', message: 'Evidence correlation completed' },
        { id: '4', timestamp: timeMinusSecs(105), type: 'WARNING', message: `Root cause identified — ${causeDesc}` },
        { id: '5', timestamp: timeMinusSecs(100), type: 'INFO', message: 'Recovery simulations generated' }
      ];
      
      if (state === 'RECOVERY' || state === 'RECOVERY_COMPLETE') {
        if (workflowActivity && workflowActivity.length > 0) {
          // Space workflow activities slightly
          workflowActivity.forEach((w, i) => {
            acts.push({
              id: `w-${i}`,
              timestamp: timeMinusSecs(60 - (i * 2)),
              type: 'INFO',
              message: w.name
            });
          });
        }
        if (state === 'RECOVERY_COMPLETE') {
          acts.push({
            id: 'r-done', timestamp: formatTime(now), type: 'SUCCESS', message: 'Recovery completed successfully.'
          });
        }
      }
    }
    
    return acts;
  }, [state, workflowActivity, incident, rootCause]);

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
