import type { ReactNode } from 'react';
import clsx from 'clsx';
import styles from './Badge.module.css';

interface BadgeProps {
  children: ReactNode;
  variant?: 'success' | 'warning' | 'critical' | 'info' | 'neutral' | 'ai';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  pulsing?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'neutral', 
  size = 'md', 
  className,
  pulsing = false 
}) => {
  return (
    <span 
      className={clsx(
        styles.badge, 
        styles[variant], 
        styles[size], 
        { [styles.pulsing]: pulsing },
        className
      )}
    >
      {children}
    </span>
  );
};
