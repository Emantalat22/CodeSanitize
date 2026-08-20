import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Code2,
  Sparkles,
  ShieldAlert,
  Bot,
  History,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';

export const Sidebar: React.FC = () => {
  const { analysisResult, transformationResult, provenanceReport } = useWorkspace();

  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: <LayoutDashboard size={16} />,
      hasBadge: analysisResult !== null,
    },
    {
      to: '/analyze',
      label: 'Analyze Code',
      icon: <Code2 size={16} />,
    },
    {
      to: '/transform',
      label: 'Transform',
      icon: <Sparkles size={16} />,
      hasBadge: transformationResult !== null,
      badgeColor: 'purple',
    },
    {
      to: '/security',
      label: 'Security',
      icon: <ShieldAlert size={16} />,
      count: analysisResult?.findings?.length,
    },
    {
      to: '/provenance',
      label: 'Provenance',
      icon: <Bot size={16} />,
      count: provenanceReport?.signals_detected?.length,
    },
    {
      to: '/history',
      label: 'Scan History',
      icon: <History size={16} />,
    },
    {
      to: '/settings',
      label: 'Settings',
      icon: <Settings size={16} />,
    },
  ];

  return (
    <aside className="sidebar-pro">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-logo-circle">
          <ShieldCheck size={18} className="logo-svg" />
        </div>
        <div className="brand-titles">
          <div className="brand-name-row">
            <span className="brand-name">CodeSanitize</span>
            <span className="brand-tag">PRO</span>
          </div>
          <span className="brand-subtitle">Static Code Intelligence</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">PLATFORM</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `nav-link-pro ${isActive ? 'active' : ''}`
            }
          >
            <span className="nav-icon-wrap">{item.icon}</span>
            <span className="nav-label-text">{item.label}</span>
            {item.count !== undefined && item.count > 0 && (
              <span className="nav-count-badge">{item.count}</span>
            )}
            {item.hasBadge && item.count === undefined && (
              <span
                className={`nav-status-dot ${
                  item.badgeColor === 'purple' ? 'dot-purple' : 'dot-teal'
                }`}
              ></span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="engine-status-box">
          <div className="engine-status-header">
            <span className="status-live-dot"></span>
            <span className="engine-label">Static AST Engine</span>
          </div>
          <span className="engine-ver">Multi-Language CIR v0.8</span>
        </div>
      </div>
    </aside>
  );
};
