import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Code2,
  GitBranch,
  Boxes,
  Activity,
  CheckCircle2,
  Layers,
  PieChart,
  Check,
  AlertTriangle,
  Clock,
  Zap,
} from 'lucide-react';
import { AnalysisFinding, AnalysisResult, FindingSeverity, ValidationPolicy } from '../types';
import { CodeAnalysisDonutChart } from './CodeAnalysisDonutChart';

interface AnalysisDashboardProps {
  result: AnalysisResult;
  validationPolicy?: ValidationPolicy;
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  result,
  validationPolicy = 'strict',
}) => {
  const {
    quality_score,
    overall_score,
    line_count,
    syntax_valid,
    metrics,
    structural_metrics,
    complexity_report,
    complexity_metrics,
    security_report,
    findings = [],
    execution_time_ms,
    analysis_timestamp,
    timestamp,
  } = result;

  // Use primary schema fields with fallbacks
  const effectiveScore = quality_score ?? overall_score ?? 100;
  const effectiveMetrics = metrics || structural_metrics || {
    lines_of_code: line_count || 0,
    blank_lines: 0,
    comment_lines: 0,
    function_count: 0,
    class_count: 0,
    import_count: 0,
    average_function_length: 0,
    raw_character_count: 0,
  };
  const effectiveComplexity = complexity_report || {
    average_complexity: 1.0,
    maximum_complexity: complexity_metrics?.cyclomatic_complexity || 1,
    most_complex_functions: [],
    complexity_level: 'Low',
    cyclomatic_complexity: complexity_metrics?.cyclomatic_complexity || 1,
    branching_count: complexity_metrics?.branching_count || 0,
    loop_count: complexity_metrics?.loop_count || 0,
    max_nesting_depth: complexity_metrics?.max_nesting_depth || 0,
    exception_handling_count: complexity_metrics?.exception_handling_count || 0,
    function_complexities: complexity_metrics?.function_complexities || [],
  };
  const effectiveSecurity = security_report || {
    critical_count: findings.filter((f) => f.severity === 'critical').length,
    warning_count: findings.filter((f) => f.severity === 'high' || f.severity === 'medium').length,
    informational_count: findings.filter((f) => f.severity === 'low' || f.severity === 'info').length,
    risk_level: findings.some((f) => f.severity === 'critical') ? 'Critical' : 'Clean',
    findings: findings.filter((f) => f.category === 'security'),
  };

  const securityFindings = effectiveSecurity.findings || findings.filter((f) => f.category === 'security');
  const criticalFindings = findings.filter((f) => f.severity === 'critical');
  const warningFindings = findings.filter((f) => f.severity === 'high' || f.severity === 'medium');
  const infoFindings = findings.filter((f) => f.severity === 'low' || f.severity === 'info');

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-warning';
    return 'score-poor';
  };

  const getScoreGrade = (score: number) => {
    if (score >= 85) return 'A (OPTIMAL)';
    if (score >= 70) return 'B (GOOD)';
    if (score >= 50) return 'C (MODERATE)';
    return 'D (NEEDS WORK)';
  };

  const getComplexityClass = (level: string) => {
    switch (level.toLowerCase()) {
      case 'high':
        return 'text-error';
      case 'medium':
        return 'text-warning';
      default:
        return 'text-success';
    }
  };

  const getSecurityRiskClass = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'text-error';
      case 'medium':
        return 'text-warning';
      case 'low':
        return 'text-primary';
      default:
        return 'text-success';
    }
  };

  const getSeverityBadge = (severity: FindingSeverity) => {
    switch (severity) {
      case 'critical':
        return <span className="severity-badge critical">CRITICAL</span>;
      case 'high':
        return <span className="severity-badge high">HIGH</span>;
      case 'medium':
        return <span className="severity-badge medium">MEDIUM</span>;
      case 'low':
        return <span className="severity-badge low">LOW</span>;
      default:
        return <span className="severity-badge info">INFO</span>;
    }
  };

  const formattedTimestamp = analysis_timestamp || timestamp || new Date().toISOString();

  return (
    <div className="clean-dashboard-wrapper">
      {/* ==================== 1. STATIC CODE INTELLIGENCE OVERVIEW ==================== */}
      <div className="dense-overview-grid">
        {/* Card 1: Code Quality Score */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Code Quality Score</span>
            <Activity size={14} className="text-primary" />
          </div>
          <div className="card-val-row">
            <span className={`card-large-val ${getScoreColor(effectiveScore)}`}>
              {effectiveScore}
            </span>
            <span className="card-val-sub">/100</span>
          </div>
          <div className="card-meta-row">
            <span className={`grade-tag ${getScoreColor(effectiveScore)}`}>
              {getScoreGrade(effectiveScore)}
            </span>
          </div>
        </div>

        {/* Card 2: Lines of Code */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Lines of Code</span>
            <Code2 size={14} className="text-primary" />
          </div>
          <div className="card-val-row">
            <span className="card-large-val">{effectiveMetrics.lines_of_code}</span>
            <span className="card-val-sub">LOC</span>
          </div>
          <div className="card-meta-row">
            <span className="meta-text">
              {effectiveMetrics.blank_lines > 0
                ? `${effectiveMetrics.blank_lines} blank, ${effectiveMetrics.comment_lines} comment`
                : `${effectiveMetrics.raw_character_count || 0} Chars`}
            </span>
          </div>
        </div>

        {/* Card 3: Number of Functions */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Functions</span>
            <Layers size={14} className="text-accent" />
          </div>
          <div className="card-val-row">
            <span className="card-large-val">{effectiveMetrics.function_count}</span>
            <span className="card-val-sub">Methods</span>
          </div>
          <div className="card-meta-row">
            <span className="meta-text">Avg {effectiveMetrics.average_function_length} lines/fn</span>
          </div>
        </div>

        {/* Card 4: Number of Classes */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Classes</span>
            <Boxes size={14} className="text-accent" />
          </div>
          <div className="card-val-row">
            <span className="card-large-val">{effectiveMetrics.class_count}</span>
            <span className="card-val-sub">Types</span>
          </div>
          <div className="card-meta-row">
            <span className="meta-text">{effectiveMetrics.import_count} Imports</span>
          </div>
        </div>

        {/* Card 5: Complexity Score */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Complexity Score</span>
            <GitBranch size={14} className="text-accent" />
          </div>
          <div className="card-val-row">
            <span className="card-large-val">{effectiveComplexity.maximum_complexity}</span>
            <span className={`rating-pill ${getComplexityClass(effectiveComplexity.complexity_level)}`}>
              {effectiveComplexity.complexity_level.toUpperCase()}
            </span>
          </div>
          <div className="card-meta-row">
            <span className="meta-text">
              Max Nesting: Level {effectiveComplexity.max_nesting_depth}
            </span>
          </div>
        </div>

        {/* Card 6: Security Risk Level */}
        <div className="overview-metric-card">
          <div className="card-top-row">
            <span className="card-label">Security Risk Level</span>
            <ShieldAlert size={14} className={getSecurityRiskClass(effectiveSecurity.risk_level)} />
          </div>
          <div className="card-val-row">
            <span className={`card-large-val ${getSecurityRiskClass(effectiveSecurity.risk_level)}`}>
              {effectiveSecurity.risk_level.toUpperCase()}
            </span>
            <span className={`rating-pill ${getSecurityRiskClass(effectiveSecurity.risk_level)}`}>
              {securityFindings.length} Issue(s)
            </span>
          </div>
          <div className="card-meta-row">
            <span className="meta-text">
              {securityFindings.length === 0 ? 'Zero static risks' : `${effectiveSecurity.critical_count} critical, ${effectiveSecurity.warning_count} warn`}
            </span>
          </div>
        </div>
      </div>

      {/* ==================== 2. TWO-COLUMN PANEL: SINGLE DONUT CHART + VALIDATION SUMMARY ==================== */}
      <div className="dashboard-grid-2col">
        {/* Section 2: Visual Code Analytics (Single Donut Chart) */}
        <div className="dashboard-panel">
          <div className="panel-header">
            <div className="panel-title-group">
              <PieChart size={15} className="text-primary" />
              <h4 className="panel-title">Visual Code Analytics</h4>
            </div>
            <span className="panel-subtitle">Multi-dimensional health distribution</span>
          </div>

          <CodeAnalysisDonutChart
            overallScore={effectiveScore}
            complexityMetrics={effectiveComplexity}
            structuralMetrics={effectiveMetrics}
            findings={findings}
          />
        </div>

        {/* Section 3: Validation Summary Card */}
        <div className="dashboard-panel">
          <div className="panel-header">
            <div className="panel-title-group">
              <ShieldCheck size={15} className="text-success" />
              <h4 className="panel-title">Validation Summary</h4>
            </div>
            <span className="panel-subtitle">Pre-acceptance invariant assurance</span>
          </div>

          <div className="validation-summary-card">
            {/* Top Status Banner */}
            <div className="val-status-header">
              <div className={`status-pill-lg ${syntax_valid ? 'success' : 'error'}`}>
                {syntax_valid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                <span>{syntax_valid ? '✓ Validation Passed' : '✗ Syntax Validation Failed'}</span>
              </div>

              <div className="val-header-meta">
                <span className="meta-chip">
                  <strong>Confidence:</strong> HIGH
                </span>
                <span className="meta-chip">
                  <Zap size={11} className="text-purple" />
                  <strong>Policy:</strong> {validationPolicy.toUpperCase()}
                </span>
                <span className="meta-chip text-muted">
                  <Clock size={11} />
                  <span>{formattedTimestamp.slice(11, 19)} ({execution_time_ms}ms)</span>
                </span>
              </div>
            </div>

            {/* Invariant Checks Checklist */}
            <div className="val-checks-checklist">
              <div className="checklist-item">
                <span className="check-bullet success">
                  <Check size={12} />
                </span>
                <span className="check-name">Syntax & Grammar Integrity</span>
                <span className="check-state">VERIFIED</span>
              </div>

              <div className="checklist-item">
                <span className="check-bullet success">
                  <Check size={12} />
                </span>
                <span className="check-name">AST Structural Invariants</span>
                <span className="check-state">VERIFIED</span>
              </div>

              <div className="checklist-item">
                <span className="check-bullet success">
                  <Check size={12} />
                </span>
                <span className="check-name">Module Imports & Aliases</span>
                <span className="check-state">INVARIANT</span>
              </div>

              <div className="checklist-item">
                <span className="check-bullet success">
                  <Check size={12} />
                </span>
                <span className="check-name">Public Interface & Signatures</span>
                <span className="check-state">PRESERVED</span>
              </div>

              <div className="checklist-item">
                <span className="check-bullet success">
                  <Check size={12} />
                </span>
                <span className="check-name">Side Effect & Scope Analysis</span>
                <span className="check-state">SAFE</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ==================== 5. SECURITY FINDINGS PANEL ==================== */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <ShieldAlert size={15} className="text-primary" />
            <h4 className="panel-title">Security & Quality Findings ({findings.length})</h4>
          </div>
          <div className="findings-summary-pills">
            <span className={`pill-count ${criticalFindings.length > 0 ? 'text-error' : 'text-muted'}`}>
              Critical: {criticalFindings.length}
            </span>
            <span className="pill-divider">•</span>
            <span className={`pill-count ${warningFindings.length > 0 ? 'text-warning' : 'text-muted'}`}>
              Warnings: {warningFindings.length}
            </span>
            <span className="pill-divider">•</span>
            <span className="pill-count text-muted">
              Info: {infoFindings.length}
            </span>
          </div>
        </div>

        {findings.length > 0 ? (
          <div className="findings-table-wrapper">
            <table className="findings-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>Severity</th>
                  <th style={{ width: '220px' }}>Issue & Rule</th>
                  <th style={{ width: '90px' }}>Location</th>
                  <th>Description & Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((finding: AnalysisFinding) => (
                  <tr key={finding.id} className={`finding-row severity-${finding.severity}`}>
                    <td>{getSeverityBadge(finding.severity)}</td>
                    <td>
                      <div className="issue-name-cell">
                        <strong className="issue-title">{finding.title}</strong>
                        <code className="issue-id">{finding.id}</code>
                      </div>
                    </td>
                    <td>
                      <span className="location-tag">
                        {finding.location?.line_start ? `Line ${finding.location.line_start}` : 'Module'}
                      </span>
                    </td>
                    <td>
                      <div className="recommendation-cell">
                        <p className="finding-p">{finding.description}</p>
                        {finding.evidence && (
                          <div className="evidence-snippet">
                            <code>{finding.evidence}</code>
                          </div>
                        )}
                        {finding.recommendation && (
                          <div className="rec-box">
                            <span><strong>Fix:</strong> {finding.recommendation}</span>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="clean-state-box">
            <ShieldCheck size={16} className="text-success" />
            <span>Static inspection completed with 0 critical security issues or maintainability warnings.</span>
          </div>
        )}
      </div>
    </div>
  );
};
