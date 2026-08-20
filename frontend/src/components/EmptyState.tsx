import React, { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  actionIcon?: ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
  actionIcon,
}) => {
  return (
    <div className="empty-state-pro">
      {icon && <div className="empty-icon-wrap">{icon}</div>}
      <h3 className="empty-title">{title}</h3>
      <p className="empty-desc">{description}</p>
      {actionText && onAction && (
        <button type="button" onClick={onAction} className="btn-primary-gradient">
          {actionIcon}
          <span>{actionText}</span>
        </button>
      )}
    </div>
  );
};
