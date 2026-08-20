import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Cpu,
  Layers,
  FileCode,
  Braces,
  Clock,
  Info,
  Hash,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { AnalysisResult } from '../types';
import { AnalysisDashboard } from './AnalysisDashboard';

interface AnalysisResultsProps {
  result: AnalysisResult;
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({ result }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'ast-metrics' | 'nonfunctional'>('dashboard');

  const {
    syntax_valid,
    analysis_status,
    parser_used,
    language,
    analysis_id,
    execution_time_ms,
    structural_metrics,
    issues,
    detected_nonfunctional_artifacts,
    capabilities,
  } = result;

  const getStatusBadge = () => {
    if (syntax_valid) {
      return (
        <div className="status-pill-lg success">
          <CheckCircle2 size={16} />
          <span>Valid Syntax</span>
        </div>
      );
    }
    if (analysis_status === 'syntax_error') {
      return (
        <div className="status-pill-lg error">
          <AlertOctagon size={16} />
          <span>Syntax Error Detected</span>
        </div>
      );
    }
    if (analysis_status === 'parser_unavailable') {
      return (
        <div className="status-pill-lg warning">
          <AlertTriangle size={16} />
          <span>Parser Unavailable</span>
        </div>
      );
    }
    return (
      <div className="status-pill-lg warning">
        <Info size={16} />
        <span>Status: {analysis_status}</span>
      </div>
    );
  };

  return (
    <div className="analysis-results-card">
      {/* Header Bar */}
      <div className="results-header">
        <div className="results-header-left">
          <div className="results-title-group">
            <Cpu className="text-primary" size={20} />
            <h3 className="results-title">Code Intelligence & Static Analysis</h3>
          </div>
          {getStatusBadge()}
        </div>

        <div className="results-header-right">
          <div className="meta-tag">
            <FileCode size={13} />
            <span>{language.toUpperCase()}</span>
          </div>
          <div className="meta-tag" title={`Engine: ${capabilities.engine_name}`}>
            <Layers size={13} />
            <span>{parser_used}</span>
          </div>
          <div className="meta-tag">
            <Clock size={13} />
            <span>{execution_time_ms}ms</span>
          </div>
          <div className="meta-tag id-tag" title={`Analysis ID: ${analysis_id}`}>
            <Hash size={12} />
            <span>{analysis_id.slice(0, 8)}...</span>
          </div>
        </div>
      </div>

      {/* Sub-Tabs: Intelligence Dashboard, AST Raw Metrics, Non-Functional Artifacts */}
      <div className="code-view-toolbar">
        <div className="tab-group">
          <button
            type="button"
            onClick={() => setActiveTab('dashboard')}
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          >
            <ShieldCheck size={15} />
            <span>Intelligence Dashboard</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('ast-metrics')}
            className={`tab-btn ${activeTab === 'ast-metrics' ? 'active' : ''}`}
          >
            <Braces size={15} />
            <span>Raw AST Metrics</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('nonfunctional')}
            className={`tab-btn ${activeTab === 'nonfunctional' ? 'active' : ''}`}
          >
            <Sparkles size={15} />
            <span>Formatting Artifacts ({detected_nonfunctional_artifacts.length})</span>
          </button>
        </div>
      </div>

      {/* Diagnostics / Syntax Issues Section (Always visible if syntax error) */}
      {issues.length > 0 && (
        <div className="results-section diagnostics-section">
          <div className="section-header">
            <AlertOctagon className="text-error" size={16} />
            <h4>Diagnostics & Syntax Errors ({issues.length})</h4>
          </div>
          <div className="diagnostics-list">
            {issues.map((issue, idx) => (
              <div
                key={idx}
                className={`diagnostic-card ${issue.severity === 'error' ? 'diag-error' : 'diag-warning'}`}
              >
                <div className="diag-header">
                  <span className="diag-rule">{issue.rule_id}</span>
                  {issue.line_start !== undefined && issue.line_start !== null && (
                    <span className="diag-location">
                      Line {issue.line_start}
                      {issue.column_start !== undefined && issue.column_start !== null && ` : Col ${issue.column_start}`}
                    </span>
                  )}
                  <span className={`diag-severity ${issue.severity}`}>
                    {issue.severity.toUpperCase()}
                  </span>
                </div>
                <p className="diag-message">{issue.message}</p>
                {Boolean(issue.metadata?.text) && (
                  <pre className="diag-snippet">{String(issue.metadata?.text)}</pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View 1: Main Code Intelligence Dashboard */}
      {activeTab === 'dashboard' && <AnalysisDashboard result={result} />}

      {/* View 2: Raw Structural Metrics Grid */}
      {activeTab === 'ast-metrics' && (
        <div className="results-section">
          <div className="section-header">
            <Braces className="text-accent" size={16} />
            <h4>AST Node Frequency & Density</h4>
          </div>
          <div className="metrics-grid">
            <div className="metric-box">
              <span className="metric-label">Lines of Code</span>
              <span className="metric-value">{structural_metrics.lines_of_code}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">AST Nodes Count</span>
              <span className="metric-value highlight">{structural_metrics.ast_nodes_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Functions & Methods</span>
              <span className="metric-value">{structural_metrics.function_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Classes & Types</span>
              <span className="metric-value">{structural_metrics.class_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Imports</span>
              <span className="metric-value">{structural_metrics.import_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Variable Declarations</span>
              <span className="metric-value">{structural_metrics.variable_assignment_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Control Flow Nodes</span>
              <span className="metric-value">{structural_metrics.control_flow_node_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Max Nesting Depth</span>
              <span className="metric-value">{structural_metrics.max_nesting_depth}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Cyclomatic Complexity</span>
              <span className="metric-value">{structural_metrics.cyclomatic_complexity}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Comments</span>
              <span className="metric-value">{structural_metrics.comment_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Docstrings</span>
              <span className="metric-value">{structural_metrics.docstring_count}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Raw Characters</span>
              <span className="metric-value">{structural_metrics.raw_character_count}</span>
            </div>
          </div>
        </div>
      )}

      {/* View 3: Non-functional Artifacts */}
      {activeTab === 'nonfunctional' && (
        <div className="results-section">
          <div className="section-header">
            <Sparkles className="text-warning" size={16} />
            <h4>Detected Non-Functional Artifacts ({detected_nonfunctional_artifacts.length})</h4>
          </div>

          {detected_nonfunctional_artifacts.length === 0 ? (
            <div className="empty-artifacts-box">
              <CheckCircle2 size={16} className="text-success" />
              <span>No special formatting or character artifacts detected. Code formatting is clean.</span>
            </div>
          ) : (
            <div className="artifacts-list">
              {detected_nonfunctional_artifacts.map((art, idx) => (
                <div key={idx} className="artifact-item-card">
                  <div className="artifact-header">
                    <span className="artifact-category-pill">{art.category}</span>
                    <span className="artifact-kind">{art.kind}</span>
                    <span className="artifact-count">Occurrences: {art.count}</span>
                  </div>
                  <p className="artifact-desc">{art.description}</p>
                  {art.unicode_code_point && (
                    <div className="artifact-meta">
                      <span>Codepoint: <code>{art.unicode_code_point}</code></span>
                    </div>
                  )}
                  {Boolean(art.details?.affected_lines && Array.isArray(art.details.affected_lines)) && (
                    <div className="artifact-lines">
                      <span className="artifact-lines-label">Lines:</span>
                      <span className="artifact-lines-val">
                        {(art.details.affected_lines as number[]).slice(0, 10).join(', ')}
                        {(art.details.affected_lines as number[]).length > 10 ? ' ...' : ''}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="artifact-disclaimer">
            <Info size={13} />
            <span>
              Non-functional properties describe formatting, whitespace, and Unicode structure.
              No watermark or AI-provenance claims are made.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
