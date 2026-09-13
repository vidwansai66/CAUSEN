import type { ReactNode } from 'react';
import clsx from 'clsx';
import styles from './Card.module.css';

interface CardProps {
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className, noPadding }) => {
  return (
    <div className={clsx(styles.card, { [styles.noPadding]: noPadding }, className)}>
      {children}
    </div>
  );
};
