import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, AlertTriangle, GitBranch, Wrench, Clock } from 'lucide-react';
import clsx from 'clsx';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: <LayoutDashboard size={20} /> },
  { path: '/live', label: 'Live Production', icon: <Activity size={20} /> },
  { path: '/incident', label: 'Incident Analysis', icon: <AlertTriangle size={20} /> },
  { path: '/simulator', label: 'Recovery Simulator', icon: <GitBranch size={20} /> },
  { path: '/actions', label: 'Maintenance / Actions', icon: <Wrench size={20} /> },
  { path: '/activity', label: 'System Activity', icon: <Clock size={20} /> },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoContainer}>
        <img src="/logo.png" alt="CAUSEN AI Logo" className={styles.logoImage} />
      </div>
      
      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx(styles.navItem, { [styles.active]: isActive })}
          >
            <span className={styles.navIcon}>{item.icon}</span>
            <span className={styles.navLabel}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.plantInfo}>
          <div className={styles.plantName}>Facility Alpha</div>
          <div className={styles.plantStatus}>Systems Online</div>
        </div>
      </div>
    </aside>
  );
};
