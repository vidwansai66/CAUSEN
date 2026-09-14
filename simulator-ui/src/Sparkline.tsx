import React from 'react';

interface SparklineProps {
  data: number[];
  color: string;
  width?: number;
  height?: number;
}

export function Sparkline({ data, color, width = 80, height = 24 }: SparklineProps) {
  if (!data || data.length < 2) return <svg width={width} height={height} />;

  // Normalize data
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  // Generate points
  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} style={{ overflow: 'visible', opacity: 0.8 }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
