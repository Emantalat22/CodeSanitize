import React from 'react';
import { useLocation } from 'react-router-dom';
import {
  RefreshCw,
  AlertCircle,
  Download,
  FileText,
  Play,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';

export const TopNavbar: React.FC = () => {
  const location = useLocation();
  const { backendHealth, runAnalysis, isAnalyzing, analysisResult } = useWorkspace();

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return { title: 'Dashboard', desc: 'Static Code Intelligence Platform Overview' };
      case '/analyze':
        return { title: 'Analyze Code', desc: 'Interactive Monaco Code Workspace & Complexity Analytics' };
      case '/transform':
        return { title: 'Transformation Studio', desc: 'Safe AST Normalization & Side-by-Side Diff' };
      case '/security':
        return { title: 'Security Findings', desc: 'Vulnerability Detection & Static Policy Compliance' };
      case '/provenance':
        return { title: 'Code Provenance', desc: 'AI-Generated Pattern Inspection & Style Metrics' };
      case '/history':
        return { title: 'Scan History', desc: 'Persistent Audit Records & Historical Scan Reports' };
      case '/settings':
        return { title: 'System Settings', desc: 'Engine Configuration & Supported Languages' };
      default:
        return { title: 'CodeSanitize', desc: 'Static Analysis Workspace' };
    }
  };

  const { title, desc } = getPageTitle();

  const handlePrint = () => {
    window.print();
  };

  const handleExportJson = () => {
    if (!analysisResult) return;
    const url = `/api/reports/export/${analysisResult.analysis_id}?format=json`;
    window.open(url, '_blank');
  };

  return (
    <header className="top-navbar-pro">
      <div className="navbar-breadcrumb">
        <h2 className="navbar-page-title">{title}</h2>
        <span className="navbar-page-desc">{desc}</span>
      </div>

      <div className="navbar-actions">
        {/* Run Quick Analysis Button */}
        <button
          type="button"
          onClick={() => runAnalysis()}
          disabled={isAnalyzing}
          className="btn-nav-action btn-analyze-quick"
          title="Run static analysis on workspace code"
        >
          <Play size={13} fill="currentColor" />
          <span>{isAnalyzing ? 'Analyzing...' : 'Analyze Code'}</span>
        </button>

        {/* Export / Print Reports */}
        <div className="export-btn-group">
          <button
            type="button"
            onClick={handlePrint}
            className="btn-nav-action btn-export-html"
            title="Generate & print comprehensive audit report"
          >
            <FileText size={13} />
            <span>Report</span>
          </button>
          {analysisResult && (
            <button
              type="button"
              onClick={handleExportJson}
              className="btn-nav-action btn-export-json"
              title="Download raw JSON telemetry payload"
            >
              <Download size={13} />
              <span>JSON</span>
            </button>
          )}
        </div>


        {/* Backend Status Indicator */}
        <div className="navbar-health-badge">
          {backendHealth.status === 'connected' ? (
            <div className="health-pill health-online" title="Backend daemon connected">
              <span className="health-dot dot-online"></span>
              <span className="health-label">API ONLINE</span>
              {backendHealth.latencyMs !== null && (
                <span className="health-latency">{backendHealth.latencyMs}ms</span>
              )}
            </div>
          ) : backendHealth.status === 'checking' ? (
            <div className="health-pill health-checking">
              <RefreshCw size={12} className="icon-spin" />
              <span>Connecting</span>
            </div>
          ) : (
            <div
              className="health-pill health-offline"
              onClick={() => backendHealth.checkHealth()}
              title="Click to retry connection"
            >
              <AlertCircle size={12} />
              <span>OFFLINE (Retry)</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
