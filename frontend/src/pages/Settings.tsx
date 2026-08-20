import React from 'react';
import {
  Server,
  Code,
  Sliders,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

import { useWorkspace } from '../context/WorkspaceContext';
import { ValidationPolicy } from '../types';

export const Settings: React.FC = () => {
  const {
    backendHealth,
    validationPolicy,
    setValidationPolicy,
    enabledRules,
    toggleRule,
  } = useWorkspace();

  const supportedLangs = [
    { name: 'Python', ext: '.py', engine: 'Native AST + Tree-sitter', status: 'Full AST + CIR + Transform' },
    { name: 'JavaScript', ext: '.js', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'TypeScript', ext: '.ts', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'Java', ext: '.java', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'C++', ext: '.cpp', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'C', ext: '.c', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'Go', ext: '.go', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'Rust', ext: '.rs', engine: 'Tree-sitter CIR', status: 'AST CIR + Metrics' },
    { name: 'Ruby', ext: '.rb', engine: 'Heuristic + Tree-sitter', status: 'AST CIR + Metrics' },
    { name: 'PHP', ext: '.php', engine: 'Heuristic + Tree-sitter', status: 'AST CIR + Metrics' },
    { name: 'C#', ext: '.cs', engine: 'Heuristic + Tree-sitter', status: 'AST CIR + Metrics' },
  ];

  const rulesList = [
    { id: 'PY-FMT-NORM-01', name: 'Formatting Normalization', desc: 'Normalizes whitespace, line breaks, and endings' },
    { id: 'PY-AST-CANON-01', name: 'AST Canonicalization', desc: 'Standardizes expression and operator layout' },
    { id: 'PY-SAFE-LOCAL-RENAME-01', name: 'Safe Local Variable Normalization', desc: 'Normalizes local intermediate variables safely' },
    { id: 'PROV-COMMENT-NORM-01', name: 'Provenance Comment Normalization', desc: 'Strips redundant obvious generated comments' },
    { id: 'PROV-STYLE-NORM-01', name: 'Provenance Style Normalization', desc: 'Standardizes spacing, padding, and blank lines' },
  ];

  return (
    <div className="page-settings-layout">
      {/* 1. System Status & Health */}
      <div className="card-pro-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <Server size={16} className="text-teal" />
            <h4>System Status & Static Engine Architecture</h4>
          </div>
          <button
            type="button"
            onClick={() => backendHealth.checkHealth()}
            className="btn-link-action"
          >
            <RefreshCw size={12} />
            <span>Check Daemon</span>
          </button>
        </div>

        <div className="settings-grid-metrics">
          <div className="setting-metric-box">
            <span className="s-label">Backend Connection</span>
            <span className={`s-val ${backendHealth.status === 'connected' ? 'text-success' : 'text-error'}`}>
              {backendHealth.status.toUpperCase()}
            </span>
            <span className="s-sub">FastAPI Daemon (port 8000)</span>
          </div>

          <div className="setting-metric-box">
            <span className="s-label">Engine Latency</span>
            <span className="s-val text-primary">
              {backendHealth.latencyMs !== null ? `${backendHealth.latencyMs} ms` : 'N/A'}
            </span>
            <span className="s-sub">Round-trip HTTP telemetry</span>
          </div>

          <div className="setting-metric-box">
            <span className="s-label">Platform Version</span>
            <span className="s-val text-purple">v0.8.0 PRO</span>
            <span className="s-sub">Static Intelligence Edition</span>
          </div>

          <div className="setting-metric-box">
            <span className="s-label">Execution Policy</span>
            <span className="s-val text-success">Zero eval/exec</span>
            <span className="s-sub">Deterministic AST Invariance</span>
          </div>
        </div>
      </div>

      {/* 2. Validation Policy & Transformation Rules */}
      <div className="card-pro-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <Sliders size={16} className="text-purple" />
            <h4>Validation Policy & Active Normalization Rules</h4>
          </div>
        </div>

        <div className="policy-selection-row">
          <label className="policy-label">Pre-Acceptance Validation Policy Mode:</label>
          <div className="policy-buttons-group">
            {(['strict', 'permissive', 'audit_only'] as ValidationPolicy[]).map((policy) => (
              <button
                key={policy}
                type="button"
                onClick={() => setValidationPolicy(policy)}
                className={`policy-choice-btn ${validationPolicy === policy ? 'active' : ''}`}
              >
                {policy.toUpperCase().replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="rules-settings-list">
          {rulesList.map((r) => {
            const isEnabled = enabledRules.includes(r.id);
            return (
              <div
                key={r.id}
                className={`rule-setting-row ${isEnabled ? 'enabled' : ''}`}
                onClick={() => toggleRule(r.id)}
              >
                <input
                  type="checkbox"
                  checked={isEnabled}
                  onChange={() => {}}
                  className="rule-checkbox"
                />
                <div className="rule-details">
                  <div className="rule-title-line">
                    <strong className="rule-name">{r.name}</strong>
                    <code className="rule-code">{r.id}</code>
                  </div>
                  <span className="rule-description">{r.desc}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Supported Languages Grid */}
      <div className="card-pro-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <Code size={16} className="text-primary" />
            <h4>Supported Multi-Language AST Parsers & CIR Extractors ({supportedLangs.length})</h4>
          </div>
          <span className="card-header-tag">100% Tree-sitter & Native AST</span>
        </div>

        <div className="languages-grid-pro">
          {supportedLangs.map((l) => (
            <div key={l.name} className="lang-card-pro">
              <div className="lang-card-header">
                <strong className="lang-name">{l.name}</strong>
                <span className="lang-ext">{l.ext}</span>
              </div>
              <div className="lang-engine">{l.engine}</div>
              <div className="lang-status">
                <CheckCircle2 size={11} className="text-success" />
                <span>{l.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
