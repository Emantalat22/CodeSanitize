import React, { useState } from 'react';
import {
  Sparkles,
  Bot,
  ArrowRight,
  ShieldCheck,
  Code2,
  FileCode,
  Layers,
  Copy,
  Check,
  Tag,
  Wand2,
  Zap,
  CheckCircle,
} from 'lucide-react';
import { ProvenanceReport } from '../types';


interface ProvenanceDashboardProps {
  report: ProvenanceReport;
  onNavigateToTransform?: () => void;
  onRemoveAIFingerprint?: () => void;
  isTransforming?: boolean;
}

export const ProvenanceDashboard: React.FC<ProvenanceDashboardProps> = ({
  report,
  onNavigateToTransform,
  onRemoveAIFingerprint,
  isTransforming = false,
}) => {
  const [copiedEvidence, setCopiedEvidence] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'naming' | 'comment' | 'boilerplate' | 'style'>('all');

  const {
    ai_pattern_score = report.provenance_score || 0,
    confidence_level = 'medium',
    confidence_score = 0.85,
    signals_detected = [],
    ai_pattern_breakdown = {},
    comment_analysis = { total_comments: 0, redundant_comments_count: 0, obvious_comments: [], comment_ratio: 0.0 },
    identifier_analysis = { generic_identifiers_count: 0, generic_identifiers: [], repeated_naming_patterns: [] },
    recommendations = [],
  } = report;

  const getScoreColor = (score: number) => {
    if (score < 30) return 'text-success';
    if (score < 65) return 'text-warning';
    return 'text-error';
  };

  const getScoreBadge = (score: number) => {
    if (score < 30) return { label: 'NATURAL / HUMAN-AUTHORED', class: 'badge-pass' };
    if (score < 65) return { label: 'MODERATE SYNTHETIC TRAITS', class: 'badge-warn' };
    return { label: 'HIGH AI PATTERN DENSITY', class: 'badge-crit' };
  };

  const scoreInfo = getScoreBadge(ai_pattern_score);

  const handleCopyEvidence = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedEvidence(text);
    setTimeout(() => setCopiedEvidence(null), 2000);
  };

  const filteredSignals = signals_detected.filter((s) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'naming') return s.signal_type.includes('naming') || s.signal_type.includes('identifier');
    if (activeFilter === 'comment') return s.signal_type.includes('comment');
    if (activeFilter === 'boilerplate') return s.signal_type.includes('boilerplate') || s.signal_type.includes('template') || s.signal_type.includes('repeated');
    if (activeFilter === 'style') return s.signal_type.includes('formatting') || s.signal_type.includes('style');
    return true;
  });

  const handleActionClick = () => {
    if (onRemoveAIFingerprint) {
      onRemoveAIFingerprint();
    } else if (onNavigateToTransform) {
      onNavigateToTransform();
    }
  };

  return (
    <div className="provenance-dashboard-container">
      {/* 1. TOP PIPELINE ACTION BANNER */}
      <div className="provenance-pipeline-banner">
        <div className="pipeline-banner-left">
          <div className="pipeline-badge">
            <Zap size={11} />
            <span>AI WATERMARK REMEDIATION PIPELINE</span>
          </div>
          <div className="pipeline-steps-indicator">
            <span className="pipeline-step-item">Scan</span>
            <span>→</span>
            <span className="pipeline-step-item">Detect</span>
            <span>→</span>
            <span className="pipeline-step-item">Transform</span>
            <span>→</span>
            <span className="pipeline-step-item">Verify</span>
            <span>→</span>
            <span className="pipeline-step-item">Recalculate Score</span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleActionClick}
          disabled={isTransforming}
          className="btn-remove-watermark"
          title="Execute automated AI watermark removal pipeline"
        >
          {isTransforming ? (
            <>
              <Sparkles size={16} className="icon-spin" />
              <span>Remediating Watermarks...</span>
            </>
          ) : (
            <>
              <Wand2 size={16} />
              <span>Remove AI Fingerprint</span>
              <ArrowRight size={14} />
            </>
          )}
        </button>
      </div>

      {/* 2. Top High-Level Metric Cards */}
      <div className="project-metrics-grid">
        <div className="project-metric-card">
          <span className="p-card-label">AI Pattern Score</span>
          <div className={`p-card-val ${getScoreColor(ai_pattern_score)}`}>
            {ai_pattern_score}
            <span style={{ fontSize: '13px', color: '#94a3b8' }}>/100</span>
          </div>
          <span className={`grade-tag ${getScoreColor(ai_pattern_score)}`} style={{ marginTop: '4px' }}>
            {scoreInfo.label}
          </span>
        </div>

        <div className="project-metric-card">
          <span className="p-card-label">Confidence Rating</span>
          <div className="p-card-val text-primary" style={{ textTransform: 'uppercase' }}>
            {Math.round(confidence_score * 100)}%
          </div>
          <span className="p-card-sub">{confidence_level.toUpperCase()} Confidence ({signals_detected.length} Signals)</span>
        </div>

        <div className="project-metric-card">
          <span className="p-card-label">Redundant Comments</span>
          <div className="p-card-val text-warning">
            {comment_analysis.redundant_comments_count}
          </div>
          <span className="p-card-sub">
            {comment_analysis.total_comments} Total Comments ({Math.round(comment_analysis.comment_ratio * 100)}% ratio)
          </span>
        </div>

        <div className="project-metric-card">
          <span className="p-card-label">Generic Identifiers</span>
          <div className="p-card-val text-purple">
            {identifier_analysis.generic_identifiers_count}
          </div>
          <span className="p-card-sub">Formulaic variable & token names</span>
        </div>
      </div>

      {/* 3. BEFORE / AFTER PROVENANCE COMPARISON PREVIEW */}
      <div className="provenance-comparison-banner">
        <div className="comparison-scores-row">
          <div className="comparison-box">
            <span className="comparison-box-label">Current AI Score</span>
            <div className={`comparison-box-val ${getScoreColor(ai_pattern_score)}`}>
              {ai_pattern_score}/100
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
            <ArrowRight size={20} className="text-purple" />
          </div>

          <div className="comparison-box">
            <span className="comparison-box-label">Target Transformed Score</span>
            <div className="comparison-box-val text-success">
              &lt; 15/100
            </div>
          </div>

          <div className="comparison-box" style={{ flexGrow: 1, minWidth: '220px' }}>
            <span className="comparison-box-label">Watermarks Queued For Removal</span>
            <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '11.5px', color: 'var(--text-secondary)' }}>
              <span>• <strong>{comment_analysis.redundant_comments_count}</strong> redundant comments</span>
              <span>• <strong>{identifier_analysis.generic_identifiers_count}</strong> generic identifiers</span>
              <span>• <strong>{ai_pattern_breakdown.boilerplate_structures_count ?? 1}</strong> structural patterns</span>
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
            Guaranteed Verification Invariants:
          </span>
          <div className="invariants-badge-list">
            <span className="invariant-pill">
              <CheckCircle size={12} />
              <span>Syntax Validation</span>
            </span>
            <span className="invariant-pill">
              <CheckCircle size={12} />
              <span>AST Equivalence</span>
            </span>
            <span className="invariant-pill">
              <CheckCircle size={12} />
              <span>Function Signature Preservation</span>
            </span>
            <span className="invariant-pill">
              <CheckCircle size={12} />
              <span>Output Equivalence</span>
            </span>
          </div>
        </div>
      </div>

      {/* 4. RECOMMENDED ACTIONS SECTION */}
      {signals_detected.length > 0 && (
        <div className="dashboard-panel">
          <div className="panel-header">
            <div className="panel-title-group">
              <Wand2 size={16} className="text-purple" />
              <h3 className="panel-title">Recommended Remediation Actions ({signals_detected.length})</h3>
            </div>
            <button
              type="button"
              onClick={handleActionClick}
              className="btn-primary-action"
              style={{ padding: '4px 12px', fontSize: '11.5px' }}
            >
              <Sparkles size={12} />
              <span>Apply All Remediations</span>
            </button>
          </div>

          <div className="recommended-actions-grid">
            {signals_detected.map((signal, idx) => {

              const isComment = signal.signal_type.includes('comment');
              const isNaming = signal.signal_type.includes('naming') || signal.signal_type.includes('identifier');

              const actionDesc = isComment
                ? 'Remove unnecessary explanatory comment'
                : isNaming
                ? 'Replace generic identifier with domain-aware human name'
                : 'Simplify textbook multi-step structure into clean inline code';

              const ruleId = isComment
                ? 'PROV-COMMENT-NORM-01'
                : isNaming
                ? 'PY-SAFE-LOCAL-RENAME-01'
                : 'PY-STRUCT-SIMPLIFY-01';

              const conf = Math.round(((signal.confidence ?? (signal as any).confidence_score) ?? 0.96) * 100);


              return (
                <div key={idx} className="action-remediation-card">
                  <div className="action-card-header">
                    <span className="action-type-pill">{signal.signal_type.replace(/_/g, ' ')}</span>
                    <span className="action-conf-pill">{conf}% Confidence</span>
                  </div>

                  <div className="action-row">
                    <span className="action-label text-error">Detected:</span>
                    <p className="action-detected-text">
                      {signal.evidence ? `"${signal.evidence}"` : signal.description}
                    </p>
                  </div>

                  <div className="action-row">
                    <span className="action-label text-success">Action:</span>
                    <p className="action-fix-text">
                      <ArrowRight size={12} className="text-success" />
                      <span>{actionDesc}</span>
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '6px', marginTop: '2px', fontSize: '10px', color: 'var(--text-muted)' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-purple)' }}>{ruleId}</span>
                    <span>{signal.file_location?.line_start ? `Line ${signal.file_location.line_start}` : 'Global Scope'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. DEDICATED AI PATTERN DETECTOR SECTION */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <Bot size={16} className="text-teal" />
            <h3 className="panel-title">AI Pattern Detector & Synthetic Signal Scanner</h3>
          </div>
          <span className="status-tag ast-ready">
            <Zap size={11} />
            <span>STATIC PATTERN ENGINE</span>
          </span>
        </div>

        {/* 6 AI Pattern Indicators Breakdown Grid */}
        <div className="category-scores-grid">
          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Repetitive Naming</span>
              <Tag size={13} className="text-purple" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.repetitive_naming_count ?? identifier_analysis.generic_identifiers_count}</span>
              <small>signals</small>
            </div>
            <p className="cat-desc">Formulaic tokens (e.g. <code>temp_value</code>, <code>result_data</code>, <code>item_1</code>).</p>
          </div>

          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Generic Comments</span>
              <FileCode size={13} className="text-warning" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.generic_comments_count ?? comment_analysis.redundant_comments_count}</span>
              <small>obvious lines</small>
            </div>
            <p className="cat-desc">Explanatory step comments stating obvious code operations.</p>
          </div>

          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Boilerplate Structures</span>
              <Layers size={13} className="text-primary" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.boilerplate_structures_count ?? 0}</span>
              <small>templates</small>
            </div>
            <p className="cat-desc">Textbook try/except logging, demo execution harnesses.</p>
          </div>

          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Predictable Templates</span>
              <Code2 size={13} className="text-teal" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.predictable_templates_count ?? 0}</span>
              <small>blocks</small>
            </div>
            <p className="cat-desc">Rigid docstring scaffolding on small trivial functions.</p>
          </div>

          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Unnatural Formatting</span>
              <Wand2 size={13} className="text-purple" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.unnatural_formatting_count ?? 0}</span>
              <small>regularities</small>
            </div>
            <p className="cat-desc">Uniform symmetry, excessive vertical padding and spacing.</p>
          </div>

          <div className="cat-score-card">
            <div className="cat-header">
              <span className="cat-title">Repeated Code Blocks</span>
              <Bot size={13} className="text-error" />
            </div>
            <div className="cat-metric">
              <span className="cat-num">{ai_pattern_breakdown.repeated_blocks_count ?? 0}</span>
              <small>duplicates</small>
            </div>
            <p className="cat-desc">Duplicate statement sequences and repetitive loops.</p>
          </div>
        </div>
      </div>

      {/* 6. Detected Provenance Signals Table */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <Bot size={15} className="text-primary" />
            <h4 className="panel-title">Detected AI Signals & Evidence ({filteredSignals.length})</h4>
          </div>

          {/* Filter Pills */}
          <div className="category-filter-tabs">
            <button
              type="button"
              onClick={() => setActiveFilter('all')}
              className={`cat-filter-pill ${activeFilter === 'all' ? 'active' : ''}`}
            >
              All Signals ({signals_detected.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('naming')}
              className={`cat-filter-pill ${activeFilter === 'naming' ? 'active' : ''}`}
            >
              Naming
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('comment')}
              className={`cat-filter-pill ${activeFilter === 'comment' ? 'active' : ''}`}
            >
              Comments
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('boilerplate')}
              className={`cat-filter-pill ${activeFilter === 'boilerplate' ? 'active' : ''}`}
            >
              Boilerplate
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('style')}
              className={`cat-filter-pill ${activeFilter === 'style' ? 'active' : ''}`}
            >
              Formatting
            </button>
          </div>
        </div>

        {filteredSignals.length > 0 ? (
          <div className="findings-table-wrapper">
            <table className="findings-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>Severity</th>
                  <th style={{ width: '220px' }}>Signal Type</th>
                  <th style={{ width: '80px' }}>Location</th>
                  <th>Description & Evidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredSignals.map((signal, idx) => (
                  <tr key={idx} className={`finding-row severity-${signal.severity}`}>
                    <td>
                      <span className={`severity-badge ${signal.severity}`}>
                        {signal.severity.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <strong>{signal.signal_type.replace(/_/g, ' ').toUpperCase()}</strong>
                    </td>
                    <td>
                      <span className="location-tag">
                        {signal.file_location?.line_start ? `L${signal.file_location.line_start}` : 'N/A'}
                      </span>
                    </td>
                    <td>
                      <p className="finding-p">{signal.description}</p>
                      {signal.evidence && (
                        <div className="evidence-snippet-box">
                          <code>{signal.evidence}</code>
                          <button
                            type="button"
                            onClick={() => handleCopyEvidence(signal.evidence || '')}
                            className="evidence-copy-btn"
                            title="Copy evidence snippet"
                          >
                            {copiedEvidence === signal.evidence ? <Check size={11} className="text-success" /> : <Copy size={11} />}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="clean-state-box">
            <ShieldCheck size={16} className="text-success" />
            <span>Zero synthetic or AI-style patterns detected for this filter. Code exhibits natural human styling.</span>
          </div>
        )}
      </div>

      {/* 7. Actionable AI Pattern Normalization Guidance */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <Sparkles size={15} className="text-purple" />
            <h4 className="panel-title">AI Pattern Normalization & Safe Transformation</h4>
          </div>
          <button
            type="button"
            onClick={handleActionClick}
            className="btn-primary-action"
            style={{ padding: '6px 14px', fontSize: '12px' }}
            title="Open Transformation Studio to execute AI Pattern Normalization"
          >
            <Wand2 size={13} />
            <span>Run AI Pattern Normalization</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <ul className="recs-list">
          {recommendations.map((rec, idx) => (
            <li key={idx} className="rec-item">
              <span className="rec-bullet">•</span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
