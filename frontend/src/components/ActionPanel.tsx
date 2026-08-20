import React, { useState } from 'react';
import {
  Play,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Sliders,
  CheckSquare,
  Square,
  Shield,
  Layers,
} from 'lucide-react';
import { SupportedLanguage, ValidationPolicy } from '../types';

interface ActionPanelProps {
  code: string;
  language: SupportedLanguage;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  onTransform: () => void;
  isTransforming: boolean;
  analysisError: string | null;
  transformError: string | null;
  enabledRules: string[];
  onToggleRule: (ruleId: string) => void;
  validationPolicy: ValidationPolicy;
  onPolicyChange: (policy: ValidationPolicy) => void;
}

const AVAILABLE_RULES = [
  {
    id: 'PY-FMT-NORM-01',
    name: 'Formatting Normalization',
    desc: 'Strip trailing whitespace, collapse excessive blank lines, standard newlines',
  },
  {
    id: 'PY-AST-CANON-01',
    name: 'AST Canonical Formatting',
    desc: 'Standardize expression layouts, operator spacing, and redundant parentheses',
  },
  {
    id: 'PY-SAFE-LOCAL-RENAME-01',
    name: 'Safe Local Variable Normalization',
    desc: 'Normalize purely function-local intermediate variables (preserves parameters & APIs)',
  },
  {
    id: 'PROV-COMMENT-NORM-01',
    name: 'Comment Provenance Normalization',
    desc: 'Safely strips redundant, obvious comments while preserving docstrings',
  },
  {
    id: 'PROV-STYLE-NORM-01',
    name: 'Style & Regularity Normalization',
    desc: 'Standardizes spacing, trailing noise, and blank line consistency',
  },
];


export const ActionPanel: React.FC<ActionPanelProps> = ({
  code,
  language,
  onAnalyze,
  isAnalyzing,
  onTransform,
  isTransforming,
  analysisError,
  transformError,
  enabledRules,
  onToggleRule,
  validationPolicy,
  onPolicyChange,
}) => {
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="action-panel">
      <div className="action-controls-row">
        <div className="action-buttons-group">
          {/* Analyze Code Button */}
          <button
            type="button"
            onClick={onAnalyze}
            disabled={!code.trim() || isAnalyzing || isTransforming}
            className="action-btn btn-analyze"
            title={`Execute deterministic AST parsing and intelligence analysis for ${language}`}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw size={15} className="icon-spin" />
                <span>Running Analysis Pipeline...</span>
              </>
            ) : (
              <>
                <Play size={15} />
                <span>Analyze Code</span>
                <span className="btn-tag active-tag">Static</span>
              </>
            )}
          </button>

          {/* Transform Code Button */}
          <button
            type="button"
            onClick={onTransform}
            disabled={!code.trim() || isAnalyzing || isTransforming}
            className="action-btn btn-transform"
            title="Execute deterministic, semantics-preserving code transformations with pre-acceptance validation"
          >
            {isTransforming ? (
              <>
                <RefreshCw size={15} className="icon-spin" />
                <span>Transforming & Validating...</span>
              </>
            ) : (
              <>
                <Sparkles size={15} />
                <span>Transform Code</span>
                <span className="btn-tag active-tag">Safe AST</span>
              </>
            )}
          </button>

          {/* Rules & Validation Policy Toggle */}
          {language === 'python' && (
            <button
              type="button"
              onClick={() => setShowConfig(!showConfig)}
              className={`toolbar-btn config-btn ${showConfig ? 'active-config' : ''}`}
              title="Configure transformation rules and validation policy"
            >
              <Sliders size={13} />
              <span>
                Engine Config ({enabledRules.length} Rules • {validationPolicy.toUpperCase()})
              </span>
            </button>
          )}
        </div>

        <div className="action-meta-info">
          <span className="meta-info-tag">
            <Layers size={12} className="text-primary" />
            <span>Target: {language.toUpperCase()}</span>
          </span>
          <span className="meta-info-tag">
            <Shield size={12} className="text-success" />
            <span>Zero Execution Security</span>
          </span>
        </div>
      </div>

      {/* Rules & Policy Selection Configuration Panel */}
      {showConfig && language === 'python' && (
        <div className="rules-config-card">
          {/* Policy Selector */}
          <div className="policy-section">
            <div className="policy-header">
              <div className="policy-title-group">
                <Shield size={15} className="text-primary" />
                <span className="policy-title">Pre-Acceptance Validation Policy:</span>
              </div>
              <span className="policy-active-badge">Active: {validationPolicy.toUpperCase()}</span>
            </div>
            <div className="policy-options-row">
              <button
                type="button"
                onClick={() => onPolicyChange('strict')}
                className={`policy-pill ${validationPolicy === 'strict' ? 'active-policy' : ''}`}
              >
                <strong>STRICT (Default)</strong>
                <span>Warnings & risk flags cause candidate rejection</span>
              </button>
              <button
                type="button"
                onClick={() => onPolicyChange('balanced')}
                className={`policy-pill ${validationPolicy === 'balanced' ? 'active-policy' : ''}`}
              >
                <strong>BALANCED</strong>
                <span>Concrete failures reject; warnings reported</span>
              </button>
              <button
                type="button"
                onClick={() => onPolicyChange('permissive')}
                className={`policy-pill ${validationPolicy === 'permissive' ? 'active-policy' : ''}`}
              >
                <strong>PERMISSIVE</strong>
                <span>Only concrete semantic invariant failures reject</span>
              </button>
            </div>
          </div>

          <div className="rules-config-header">
            <h4>Enabled Semantics-Preserving Transformation Rules</h4>
            <span className="config-badge">Pre-Acceptance Validated</span>
          </div>
          <div className="rules-checkbox-list">
            {AVAILABLE_RULES.map((rule) => {
              const isEnabled = enabledRules.includes(rule.id);
              return (
                <div
                  key={rule.id}
                  onClick={() => onToggleRule(rule.id)}
                  className={`rule-option-item ${isEnabled ? 'selected' : ''}`}
                >
                  <div className="rule-checkbox">
                    {isEnabled ? (
                      <CheckSquare size={15} className="text-success" />
                    ) : (
                      <Square size={15} className="text-muted" />
                    )}
                  </div>
                  <div className="rule-info">
                    <div className="rule-title-row">
                      <span className="rule-name">{rule.name}</span>
                      <code className="rule-id-code">{rule.id}</code>
                    </div>
                    <p className="rule-desc">{rule.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error Alerts */}
      {analysisError && (
        <div className="error-banner">
          <AlertCircle size={16} className="text-error" />
          <div className="error-banner-text">
            <strong>Analysis Diagnostic:</strong> {analysisError}
          </div>
        </div>
      )}

      {transformError && (
        <div className="error-banner">
          <AlertCircle size={16} className="text-error" />
          <div className="error-banner-text">
            <strong>Transformation Diagnostic:</strong> {transformError}
          </div>
        </div>
      )}
    </div>
  );
};
