import React, { useState, useEffect } from 'react';
import { Bell, User, Sun, Moon } from 'lucide-react';
import { useDemoState } from '../../hooks/useDemoState';
import { useTheme } from '../../hooks/useTheme';
import { Badge } from '../common/Badge';
import { VapiVoiceButton } from '../common/VapiVoiceButton';
import styles from './Topbar.module.css';

export const Topbar: React.FC = () => {
  const { state, incident } = useDemoState();
  const { theme, toggleTheme } = useTheme();
  
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const getStatusDisplay = () => {
    switch (state) {
      case 'NORMAL': return { label: 'SYSTEM HEALTHY', color: 'success' };
      case 'WARNING': return { label: 'SYSTEM WARNING', color: 'warning' };
      case 'CRITICAL': return { label: 'CRITICAL INCIDENT', color: 'critical' };
      case 'RECOVERY': return { label: 'RECOVERY IN PROGRESS', color: 'ai' };
      case 'RECOVERY_COMPLETE': return { label: 'SYSTEM RECOVERED', color: 'success' };
      default: return { label: 'SYSTEM HEALTHY', color: 'success' };
    }
  };

  const status = getStatusDisplay();

  return (
    <header className={styles.topbar}>
      <div className={styles.pageInfo}>
        <div className={styles.facilityContext}>
          <span className={styles.facilityName}>FACILITY ALPHA</span>
          <span className={styles.lineName}>LINE 2</span>
        </div>
        <div className={styles.statusWrapper}>
          <Badge variant="neutral" className={styles.demoBadge}>DEMO MODE</Badge>
          <div className={`${styles.statusIndicator} ${styles[status.color]}`}>
            <span className={styles.statusDot}>●</span>
            <span className={styles.statusText}>{status.label}</span>
          </div>
          {incident && incident.status === 'ACTIVE' && (
            <span className={styles.incidentRef}>{incident.id}</span>
          )}
          <span className={styles.timestamp}>{currentTime}</span>
        </div>
      </div>

      <div className={styles.actions}>

        
        <button className={styles.iconBtn} onClick={toggleTheme} aria-label="Toggle Theme">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <button className={styles.iconBtn}>
          <Bell size={20} />
          {['WARNING', 'CRITICAL'].includes(state) && <span className={styles.indicator} />}
        </button>
        
        <VapiVoiceButton />
        
        <div className={styles.userProfile}>
          <div className={styles.avatar}>
            <User size={18} />
          </div>
          <div className={styles.userDetails}>
            <span className={styles.userName}>Oper. J. Smith</span>
            <span className={styles.userRole}>Shift Supervisor</span>
          </div>
        </div>
      </div>
    </header>
  );
};
