import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { DemoController } from '../common/DemoController';
import styles from './AppShell.module.css';

export const AppShell: React.FC = () => {
  const [showIntro, setShowIntro] = useState(true);

  useEffect(() => {
    // The animation takes about 1.5s total.
    const timer = setTimeout(() => {
      setShowIntro(false);
    }, 1800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={styles.appShell}>
      {showIntro && (
        <div className={styles.cinematicOverlay}>
          <img 
            src="/causen-brand-logo.png" 
            alt="CAUSEN AI Cinematic Entry" 
            className={styles.cinematicLogo} 
          />
        </div>
      )}
      
      <Sidebar />
      <div className={styles.mainWrapper}>
        <Topbar />
        <main className={styles.mainContent}>
          <div className={styles.pageContainer}>
            <Outlet />
          </div>
        </main>
      </div>
      <DemoController />
    </div>
  );
};
