import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  Sparkles,
  ShieldAlert,
  Activity,
} from 'lucide-react';

import { useWorkspace } from '../context/WorkspaceContext';
import { CodeEditor } from '../components/CodeEditor';
import { AnalysisDashboard } from '../components/AnalysisDashboard';
import { FindingTable } from '../components/FindingTable';
import { SupportedLanguage } from '../types';

const EXTENSIONS: Record<string, string> = {
  python: '.py',
  javascript: '.js',
  typescript: '.ts',
  java: '.java',
  cpp: '.cpp',
  c: '.c',
  go: '.go',
  rust: '.rs',
  ruby: '.rb',
  php: '.php',
  csharp: '.cs',
  auto: '.py',
};

export const Analyze: React.FC = () => {
  const navigate = useNavigate();
  const {
    code,
    setCode,
    language,
    setLanguage,
    filename,
    setFilename,
    analysisResult,
    isAnalyzing,
    analysisError,
    runAnalysis,
    runTransform,
    isTransforming,
    validationPolicy,
  } = useWorkspace();

  const [activeTab, setActiveTab] = useState<'findings' | 'recommendations'>('findings');

  const handleLanguageChange = (newLang: SupportedLanguage) => {
    setLanguage(newLang);
    const ext = EXTENSIONS[newLang] || '.txt';
    const baseName = filename.includes('.') ? filename.substring(0, filename.lastIndexOf('.')) : filename;
    setFilename(`${baseName || 'main'}${ext}`);
  };

  const handleTransformClick = async () => {
    await runTransform();
    navigate('/transform');
  };

  return (
    <div className="page-analyze-layout">
      {/* Left Column: Code Editor & Action Bar */}
      <div className="analyze-editor-col">
        {/* Central Code Editor */}
        <div className="editor-panel-wrapper">
          <CodeEditor
            code={code}
            onChange={setCode}
            language={language}
            onLanguageChange={handleLanguageChange}
            filename={filename}
            onFilenameChange={setFilename}
          />
        </div>

        {/* Action Toolbar */}
        <div className="analyze-action-bar">
          <div className="action-buttons-left">
            <button
              type="button"
              onClick={() => runAnalysis()}
              disabled={isAnalyzing}
              className="btn-primary-action"
            >
              <Play size={14} fill="currentColor" />
              <span>{isAnalyzing ? 'Analyzing AST...' : 'Analyze Code'}</span>
            </button>

            <button
              type="button"
              onClick={handleTransformClick}
              disabled={isTransforming}
              className="btn-secondary-action"
            >
              <Sparkles size={14} className={isTransforming ? 'icon-spin' : ''} />
              <span>{isTransforming ? 'Transforming...' : 'Transform Code'}</span>
            </button>
          </div>

          <div className="action-meta-right">
            <span className="meta-policy-tag">Policy: <strong>{validationPolicy.toUpperCase()}</strong></span>
            <span className="meta-lang-tag">{language.toUpperCase()}</span>
          </div>
        </div>

        {analysisError && (
          <div className="error-alert-banner">
            <span>{analysisError}</span>
          </div>
        )}

        {/* Bottom Findings Drawer */}
        {analysisResult && (
          <div className="analyze-bottom-panel">
            <div className="bottom-tabs-header">
              <button
                type="button"
                onClick={() => setActiveTab('findings')}
                className={`bottom-tab ${activeTab === 'findings' ? 'active' : ''}`}
              >
                <ShieldAlert size={14} />
                <span>Security & Quality Findings ({analysisResult.findings?.length || 0})</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('recommendations')}
                className={`bottom-tab ${activeTab === 'recommendations' ? 'active' : ''}`}
              >
                <Activity size={14} />
                <span>Recommendations ({analysisResult.recommendations?.length || 0})</span>
              </button>
            </div>

            <div className="bottom-tab-body">
              {activeTab === 'findings' && (
                <FindingTable
                  findings={analysisResult.findings}
                  emptyMessage="No security issues or critical warnings detected in this file."
                />
              )}

              {activeTab === 'recommendations' && (
                <ul className="recs-list-pro">
                  {analysisResult.recommendations?.map((rec, idx) => (
                    <li key={idx} className="rec-item-pro">
                      <span className="rec-bullet-pro">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Static Intelligence Sidebar */}
      <div className="analyze-sidebar-col">
        {analysisResult ? (
          <AnalysisDashboard
            result={analysisResult}
            validationPolicy={validationPolicy}
          />
        ) : (
          <div className="empty-sidebar-prompt">
            <Activity size={32} className="text-muted" />
            <h4>Static Intelligence Ready</h4>
            <p>Click <strong>Analyze Code</strong> to view metrics, cyclomatic complexity, and security findings.</p>
          </div>
        )}
      </div>
    </div>
  );
};
