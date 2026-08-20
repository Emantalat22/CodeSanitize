import React, { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'error' | 'info' | 'purple';
  };
  icon?: ReactNode;
  valueColor?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  badge,
  icon,
  valueColor,
  onClick,
}) => {
  return (
    <div
      className={`metric-card-pro ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="metric-header-row">
        <span className="metric-label">{label}</span>
        {icon && <div className="metric-icon-wrap">{icon}</div>}
      </div>

      <div className="metric-value-row">
        <span className="metric-val" style={{ color: valueColor || '#fff' }}>
          {value}
        </span>
        {badge && (
          <span className={`metric-badge badge-${badge.variant}`}>
            {badge.text}
          </span>
        )}
      </div>

      {subtext && <div className="metric-subtext">{subtext}</div>}
    </div>
  );
};
