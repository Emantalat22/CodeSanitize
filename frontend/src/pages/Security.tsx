import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  Lock,
} from 'lucide-react';

import { useWorkspace } from '../context/WorkspaceContext';
import { MetricCard } from '../components/MetricCard';
import { FindingTable } from '../components/FindingTable';

export const Security: React.FC = () => {
  const { analysisResult } = useWorkspace();
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  const securityReport = analysisResult?.security_report;
  const findings = analysisResult?.findings || [];
  const riskLevel = securityReport?.risk_level || 'low';

  const criticalCount = findings.filter((f) => f.severity.toLowerCase() === 'critical').length;
  const highCount = findings.filter((f) => f.severity.toLowerCase() === 'high').length;
  const mediumCount = findings.filter((f) => f.severity.toLowerCase() === 'medium').length;
  const lowCount = findings.filter((f) => f.severity.toLowerCase() === 'low' || f.severity.toLowerCase() === 'info').length;

  const filteredFindings = findings.filter((f) => {
    if (filterSeverity === 'all') return true;
    return f.severity.toLowerCase() === filterSeverity;
  });

  return (
    <div className="page-security-layout">
      {/* 1. Security Overview Metric Cards */}
      <div className="dashboard-grid-cards">
        <MetricCard
          label="Security Risk Rating"
          value={riskLevel.toUpperCase()}
          subtext="Static AST vulnerability posture"
          valueColor={riskLevel === 'low' ? '#10b981' : riskLevel === 'medium' ? '#f59e0b' : '#f43f5e'}
          icon={<Lock size={16} className="text-teal" />}
        />

        <MetricCard
          label="Critical Severity"
          value={criticalCount}
          subtext="Remote execution / eval risks"
          valueColor={criticalCount > 0 ? '#f43f5e' : '#10b981'}
          badge={criticalCount > 0 ? { text: 'ACTION REQUIRED', variant: 'error' } : undefined}
          icon={<ShieldAlert size={16} className="text-error" />}
        />

        <MetricCard
          label="High Severity"
          value={highCount}
          subtext="Shell injection & unsafe subprocess"
          valueColor={highCount > 0 ? '#f59e0b' : '#10b981'}
          icon={<AlertTriangle size={16} className="text-warning" />}
        />

        <MetricCard
          label="Medium / Low Findings"
          value={mediumCount + lowCount}
          subtext="Informational & best practice issues"
          icon={<Info size={16} className="text-primary" />}
        />
      </div>

      {/* 2. Security Findings Table Panel with Severity Filters */}
      <div className="dashboard-findings-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <ShieldAlert size={16} className="text-error" />
            <h4>Detected Security Vulnerabilities & AST Rule Violations ({findings.length})</h4>
          </div>

          <div className="severity-filter-tabs">
            <button
              type="button"
              onClick={() => setFilterSeverity('all')}
              className={`filter-tab ${filterSeverity === 'all' ? 'active' : ''}`}
            >
              All ({findings.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterSeverity('critical')}
              className={`filter-tab tab-crit ${filterSeverity === 'critical' ? 'active' : ''}`}
            >
              Critical ({criticalCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterSeverity('high')}
              className={`filter-tab tab-high ${filterSeverity === 'high' ? 'active' : ''}`}
            >
              High ({highCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterSeverity('medium')}
              className={`filter-tab tab-med ${filterSeverity === 'medium' ? 'active' : ''}`}
            >
              Medium ({mediumCount})
            </button>
            <button
              type="button"
              onClick={() => setFilterSeverity('low')}
              className={`filter-tab tab-low ${filterSeverity === 'low' ? 'active' : ''}`}
            >
              Low/Info ({lowCount})
            </button>
          </div>
        </div>

        <FindingTable
          findings={filteredFindings}
          emptyMessage="No security vulnerabilities detected matching this severity filter."
        />
      </div>

      {/* 3. Static Security Policy Overview */}
      <div className="card-pro-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <ShieldCheck size={16} className="text-success" />
            <h4>Deterministic Security Policy Rules</h4>
          </div>
          <span className="card-header-tag">Zero Dynamic Execution</span>
        </div>

        <div className="security-rules-grid">
          <div className="sec-rule-item">
            <span className="rule-badge rule-crit">SEC-PY-001</span>
            <div className="rule-info">
              <strong>Dynamic Code Evaluation (eval / exec)</strong>
              <p>Flags any dynamic invocation of Python interpreter evaluation functions that accept arbitrary strings.</p>
            </div>
          </div>

          <div className="sec-rule-item">
            <span className="rule-badge rule-crit">SEC-PY-002</span>
            <div className="rule-info">
              <strong>Subprocess Shell Execution (shell=True)</strong>
              <p>Flags system command execution where shell interpretation enables command injection.</p>
            </div>
          </div>

          <div className="sec-rule-item">
            <span className="rule-badge rule-med">SEC-PY-003</span>
            <div className="rule-info">
              <strong>Unsafe Object Deserialization (pickle / marshal)</strong>
              <p>Detects untrusted deserialization APIs that can lead to arbitrary object instantiation.</p>
            </div>
          </div>

          <div className="sec-rule-item">
            <span className="rule-badge rule-low">SEC-PY-004</span>
            <div className="rule-info">
              <strong>Insecure Temporary File Generation</strong>
              <p>Identifies predictable file creation paths prone to symlink races and permissions exposure.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
