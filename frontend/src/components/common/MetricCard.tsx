import type { ReactNode } from 'react';
import { Card } from './Card';
import clsx from 'clsx';
import styles from './MetricCard.module.css';

interface MetricCardProps {
  title: string;
  value: string | number | ReactNode;
  subtitle?: string;
  trend?: {
    value: string;
    direction: 'up' | 'down' | 'neutral';
    label?: string;
  };
  icon?: ReactNode;
  intent?: 'neutral' | 'success' | 'warning' | 'critical';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  intent = 'neutral',
  className
}) => {
  return (
    <Card className={clsx(styles.metricCard, styles[intent], className)}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {icon && <div className={styles.icon}>{icon}</div>}
      </div>
      <div className={styles.content}>
        <div className={styles.value}>{value}</div>
        {trend && (
          <div className={clsx(styles.trend, styles[`trend-${trend.direction}`])}>
            <span>{trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : '→'} {trend.value}</span>
            {trend.label && <span className={styles.trendLabel}>{trend.label}</span>}
          </div>
        )}
      </div>
      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
    </Card>
  );
};
