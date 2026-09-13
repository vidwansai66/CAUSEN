import { useDemoState } from '../../hooks/useDemoState';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { CheckCircle2, CircleDashed, Loader2, XCircle } from 'lucide-react';
import styles from './MaintenanceActions.module.css';

export default function MaintenanceActions() {
  const { state, selectedActionId, recoveryActions, workflowActivity, incident, rootCause } = useDemoState();

  const getActions = () => {

    const selectedAction = recoveryActions?.find(a => a.id === selectedActionId) || recoveryActions?.[0];
    
    // Convert backend workflowActivity into UI format
    if (workflowActivity && workflowActivity.length > 0) {
      return workflowActivity.map(w => ({
        id: `ACT-${w.id}`,
        title: w.name,
        target: w.target,
        status: w.status,
        time: w.timestamp
      }));
    }

    if (state === 'NORMAL' || state === 'WARNING' || state === 'CRITICAL') {
      return [
        { id: 'ACT-001', title: 'Routine Sensor Calibration', target: 'M01', status: 'COMPLETED', time: '08:15' },
        { id: 'ACT-002', title: 'Firmware Update', target: 'M05', status: 'COMPLETED', time: '09:30' },
      ];
    }
    if (state === 'RECOVERY') {
      return [
        { id: selectedAction?.id || 'ACT-XXX', title: selectedAction?.title || 'WORKLOAD REDISTRIBUTION', target: 'System', status: 'EXECUTING', time: 'Just now' },
        { id: 'ACT-005', title: 'OPERATOR NOTIFICATION', target: 'System', status: 'COMPLETED', time: 'Just now' },
      ];
    }
    if (state === 'RECOVERY_COMPLETE') {
      return [
        { id: selectedAction?.id || 'ACT-XXX', title: selectedAction?.title || 'WORKLOAD REDISTRIBUTION', target: 'System', status: 'COMPLETED', time: 'Just now' },
        { id: 'ACT-004', title: `MAINTENANCE TICKET (${incident?.affectedMachineId || 'System'} ${rootCause?.description || 'Maintenance'})`, target: incident?.affectedMachineId || 'System', status: 'EXECUTING', time: 'Just now' },
        { id: 'ACT-005', title: 'OPERATOR NOTIFICATION', target: 'System', status: 'COMPLETED', time: 'Just now' },
      ];
    }
    return [];
  };


  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className={styles.iconCompleted} />;
      case 'EXECUTING': return <Loader2 className={styles.iconExecuting} />;
      case 'FAILED': return <XCircle className={styles.iconFailed} />;
      default: return <CircleDashed className={styles.iconPending} />;
    }
  };

  const actions = getActions();

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Maintenance & Actions</h2>
        <p className={styles.subtitle}>Track system automated workflows and manual interventions.</p>
      </div>

      <Card className={styles.actionList}>
        {actions.map(action => (
          <div key={action.id} className={styles.actionRow}>
            <div className={styles.actionMain}>
              {getStatusIcon(action.status)}
              <div className={styles.actionInfo}>
                <h4>{action.title}</h4>
                <div className={styles.actionMeta}>
                  <span>Target: <strong>{action.target}</strong></span>
                  <span>ID: {action.id}</span>
                </div>
              </div>
            </div>
            
            <div className={styles.actionEnd}>
              <div className={styles.time}>{action.time}</div>
              <Badge 
                variant={
                  action.status === 'COMPLETED' ? 'success' : 
                  action.status === 'EXECUTING' ? 'info' : 
                  action.status === 'FAILED' ? 'critical' : 'neutral'
                }
                pulsing={action.status === 'EXECUTING'}
              >
                {action.status}
              </Badge>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
