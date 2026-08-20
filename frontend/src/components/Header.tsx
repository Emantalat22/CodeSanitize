import React from 'react';
import {
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  Code2,
  Sparkles,
  Bot,
  FolderArchive,
  History,
  Download,
  FileText,
} from 'lucide-react';

import { BackendHealthState } from '../hooks/useBackendHealth';

interface HeaderProps {
  health: BackendHealthState;
  activeView: 'editor' | 'transform' | 'provenance' | 'project' | 'history';
  onViewChange: (view: 'editor' | 'transform' | 'provenance' | 'project' | 'history') => void;
  hasAnalysis: boolean;
  hasTransformation: boolean;
  onExportReport?: (format: 'html' | 'json') => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  activeView,
  onViewChange,
  hasAnalysis,
  hasTransformation,
  onExportReport,
}) => {
  const getStatusBadge = () => {
    switch (health.status) {
      case 'connected':
        return (
          <div
            className="status-badge status-connected"
            title={`API Connected: ${health.data?.app || 'CodeSanitize'} v${health.data?.version || '0.7.0'}`}
          >
            <span className="status-dot connected"></span>
            <span className="status-label">API Online</span>
            {health.latencyMs !== null && (
              <span className="status-latency">{health.latencyMs}ms</span>
            )}
          </div>
        );
      case 'checking':
        return (
          <div className="status-badge status-checking">
            <RefreshCw className="icon-spin" size={13} />
            <span className="status-label">Connecting...</span>
          </div>
        );
      case 'disconnected':
      default:
        return (
          <div
            className="status-badge status-disconnected"
            title={health.error || 'Cannot reach backend service'}
          >
            <AlertCircle size={13} />
            <span className="status-label">Offline</span>
            <button
              onClick={() => health.checkHealth()}
              className="retry-btn"
              title="Retry connection"
            >
              Retry
            </button>
          </div>
        );
    }
  };

  return (
    <header className="app-header">
      <div className="header-container">
        {/* Left: Branding */}
        <div className="brand-section">
          <div className="logo-icon-wrapper">
            <ShieldCheck className="logo-icon" size={20} />
          </div>
          <div className="brand-text">
            <div className="brand-title-row">
              <span className="brand-title">CodeSanitize</span>
              <span className="badge-version">v0.7.0</span>
            </div>
            <span className="brand-tagline">Deterministic Static Code Intelligence</span>
          </div>
        </div>

        {/* Center: Navigation View Tabs */}
        <nav className="header-nav">
          <button
            type="button"
            onClick={() => onViewChange('editor')}
            className={`nav-tab ${activeView === 'editor' ? 'active' : ''}`}
          >
            <Code2 size={14} />
            <span>Workspace</span>
            {hasAnalysis && <span className="tab-dot active-dot" title="Analysis available"></span>}
          </button>

          <button
            type="button"
            onClick={() => onViewChange('transform')}
            className={`nav-tab ${activeView === 'transform' ? 'active' : ''}`}
          >
            <Sparkles size={14} />
            <span>Transformation</span>
            {hasTransformation && <span className="tab-dot purple-dot" title="Transformed code ready"></span>}
          </button>

          <button
            type="button"
            onClick={() => onViewChange('provenance')}
            className={`nav-tab ${activeView === 'provenance' ? 'active' : ''}`}
          >
            <Bot size={14} />
            <span>Code Provenance</span>
          </button>

          <button
            type="button"
            onClick={() => onViewChange('project')}
            className={`nav-tab ${activeView === 'project' ? 'active' : ''}`}
          >
            <FolderArchive size={14} />
            <span>Project Audit</span>
          </button>

          <button
            type="button"
            onClick={() => onViewChange('history')}
            className={`nav-tab ${activeView === 'history' ? 'active' : ''}`}
          >
            <History size={14} />
            <span>Scan History</span>
          </button>
        </nav>


        {/* Right: Actions & Health Status */}
        <div className="header-actions">
          {onExportReport && hasAnalysis && (
            <div className="report-export-group">
              <button
                type="button"
                onClick={() => onExportReport('html')}
                className="export-btn btn-html"
                title="Export print-ready HTML report"
              >
                <FileText size={13} />
                <span>HTML Report</span>
              </button>
              <button
                type="button"
                onClick={() => onExportReport('json')}
                className="export-btn btn-json"
                title="Export raw JSON telemetry"
              >
                <Download size={13} />
                <span>JSON</span>
              </button>
            </div>
          )}

          <div className="api-status-group">
            {getStatusBadge()}
          </div>
        </div>
      </div>
    </header>
  );
};
