import React from 'react';

interface StatusBadgeProps {
  type: 'pass' | 'warn' | 'fail' | 'info' | 'high' | 'medium' | 'low' | 'connected' | 'disconnected';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  type,
  label,
  size = 'md',
}) => {
  const displayLabel = label || type.toUpperCase();

  const getStyleClass = () => {
    switch (type.toLowerCase()) {
      case 'pass':
      case 'low':
      case 'connected':
        return 'status-badge-pass';
      case 'warn':
      case 'medium':
        return 'status-badge-warn';
      case 'fail':
      case 'high':
      case 'disconnected':
        return 'status-badge-fail';
      case 'info':
      default:
        return 'status-badge-info';
    }
  };

  return (
    <span className={`status-badge-pill ${getStyleClass()} size-${size}`}>
      {displayLabel}
    </span>
  );
};
