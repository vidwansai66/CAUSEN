import { useState, useEffect } from 'react';
import { Settings2, RotateCcw, Zap } from 'lucide-react';
import { useDemoState } from '../../hooks/useDemoState';
import { API_BASE_URL } from '../../config';
import styles from './DemoController.module.css';

export const DemoController: React.FC = () => {
  const { state, connectionStatus } = useDemoState();
  const [isVisible, setIsVisible] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl + Shift + D to toggle demo controller
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'd') {
        setIsVisible(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleInjectFault = async () => {
    setIsInjecting(true);
    try {
      await fetch(`${API_BASE_URL}/api/fault/inject`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
    } catch (e) {
      console.error(e);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await fetch(`${API_BASE_URL}/api/fault/reset`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    } finally {
      setIsResetting(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className={styles.container}>
      <div className={styles.handle}>DEMO MENU (Ctrl+Shift+D) - {connectionStatus}</div>
      <div className={styles.menu}>
        <div style={{ marginBottom: '8px', color: '#fff', fontSize: '12px' }}>
          Current Backend State: <strong>{state}</strong>
        </div>
        <button className={styles.button} onClick={handleReset}>
          RESET TO HEALTHY
        </button>
        <button className={`${styles.button} ${styles.active}`} onClick={handleInject}>
          INJECT M03 FAULT
        </button>
      </div>
    </div>
  );
};
