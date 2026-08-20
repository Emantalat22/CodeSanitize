import React, { useState } from 'react';
import {
  FolderArchive,
  Upload,
  FileCode,
  Layers,
  ShieldCheck,
  Activity,
  AlertCircle,
  Copy,
} from 'lucide-react';

import { ProjectAnalysisResult } from '../types';
import { analyzeProject, uploadProjectZip } from '../services/api';

export const ProjectAuditView: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectResult, setProjectResult] = useState<ProjectAnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<'files' | 'duplications' | 'recommendations'>('files');

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const res = await uploadProjectZip(file, file.name.replace(/\.[^/.]+$/, ''));
      setProjectResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze project archive');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSampleProject = async () => {
    setIsUploading(true);
    setError(null);

    try {
      const sampleFiles = [
        {
          filename: 'src/pricing.py',
          code: `def calculate_discount(price, tier):\n    if tier == "vip":\n        return price * 0.8\n    elif tier == "gold":\n        return price * 0.9\n    return price\n`,
          language: 'python',
        },
        {
          filename: 'src/billing.py',
          code: `def calculate_discount_clone(price, tier):\n    if tier == "vip":\n        return price * 0.8\n    elif tier == "gold":\n        return price * 0.9\n    return price\n`,
          language: 'python',
        },
        {
          filename: 'src/api/auth.ts',
          code: `export function verifyToken(token: string): boolean {\n    return token.startsWith("ey") && token.length > 20;\n}\n`,
          language: 'typescript',
        },
        {
          filename: 'pkg/worker/job.go',
          code: `package worker\n\nfunc DispatchJob(id string) bool {\n    return len(id) > 0\n}\n`,
          language: 'go',
        },
      ];

      const res = await analyzeProject({
        project_name: 'ECommerce Microservices',
        files: sampleFiles,
      });
      setProjectResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run sample project analysis');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="project-audit-container">
      {/* Top Banner & Upload Controls */}
      <div className="project-upload-card">
        <div className="upload-left">
          <div className="upload-icon-box">
            <FolderArchive size={28} className="text-primary" />
          </div>
          <div>
            <h3 className="upload-title">Multi-File Project Intelligence</h3>
            <p className="upload-subtitle">
              Upload a ZIP archive or run static multi-language analysis across repository source files.
            </p>
          </div>
        </div>

        <div className="upload-right">
          <label className="upload-btn primary-upload">
            <Upload size={14} />
            <span>{isUploading ? 'Scanning Project...' : 'Upload Project ZIP'}</span>
            <input
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={isUploading}
              style={{ display: 'none' }}
            />
          </label>

          <button
            type="button"
            onClick={handleLoadSampleProject}
            disabled={isUploading}
            className="upload-btn secondary-upload"
          >
            <Layers size={14} />
            <span>Load Sample Multi-Lang Repo</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={16} className="text-error" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {projectResult && (
        <div className="project-results-wrapper">
          {/* Top Summary Metrics */}
          <div className="project-metrics-grid">
            <div className="project-metric-card">
              <span className="p-card-label">Project Health Score</span>
              <div className="p-card-val text-success">{projectResult.overall_quality_score}/100</div>
              <span className="p-card-sub">{projectResult.project_name}</span>
            </div>

            <div className="project-metric-card">
              <span className="p-card-label">Source Files</span>
              <div className="p-card-val text-primary">{projectResult.total_files}</div>
              <span className="p-card-sub">{projectResult.total_lines_of_code} Total LOC</span>
            </div>

            <div className="project-metric-card">
              <span className="p-card-label">Code Duplications</span>
              <div className="p-card-val text-warning">{projectResult.duplications.length}</div>
              <span className="p-card-sub">Clones Detected</span>
            </div>

            <div className="project-metric-card">
              <span className="p-card-label">Security Risk</span>
              <div
                className={`p-card-val ${
                  projectResult.security_summary.risk_level === 'Clean' ? 'text-success' : 'text-error'
                }`}
              >
                {projectResult.security_summary.risk_level}
              </div>
              <span className="p-card-sub">{projectResult.security_summary.critical_count} Critical Issues</span>
            </div>
          </div>

          {/* Sub Navigation Tabs */}
          <div className="project-sub-tabs">
            <button
              type="button"
              onClick={() => setActiveTab('files')}
              className={`p-tab ${activeTab === 'files' ? 'active' : ''}`}
            >
              <FileCode size={14} />
              <span>Analyzed Files ({projectResult.files.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('duplications')}
              className={`p-tab ${activeTab === 'duplications' ? 'active' : ''}`}
            >
              <Copy size={14} />
              <span>Duplicate Code Clones ({projectResult.duplications.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('recommendations')}
              className={`p-tab ${activeTab === 'recommendations' ? 'active' : ''}`}
            >
              <Activity size={14} />
              <span>Architecture Recommendations ({projectResult.recommendations.length})</span>
            </button>
          </div>

          {/* Tab 1: Analyzed Files Table */}
          {activeTab === 'files' && (
            <div className="dashboard-panel">
              <div className="findings-table-wrapper">
                <table className="findings-table">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Language</th>
                      <th>Lines of Code</th>
                      <th>Quality Score</th>
                      <th>Complexity</th>
                      <th>Security Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projectResult.files.map((f, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>{f.filename}</strong>
                        </td>
                        <td>
                          <span className="lang-pill">{f.language.toUpperCase()}</span>
                        </td>
                        <td>{f.lines_of_code} LOC</td>
                        <td>
                          <span
                            className={
                              f.quality_score >= 80
                                ? 'text-success'
                                : f.quality_score >= 60
                                ? 'text-warning'
                                : 'text-error'
                            }
                          >
                            {f.quality_score}/100
                          </span>
                        </td>
                        <td>{f.complexity_level}</td>
                        <td>
                          <span className={f.security_risk === 'Clean' ? 'text-success' : 'text-error'}>
                            {f.security_risk}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Duplication Findings */}
          {activeTab === 'duplications' && (
            <div className="dashboard-panel">
              {projectResult.duplications.length > 0 ? (
                <div className="duplications-list">
                  {projectResult.duplications.map((d, idx) => (
                    <div key={idx} className="dup-item-card">
                      <div className="dup-header">
                        <div className="dup-type-badge">
                          {d.duplicate_type.replace('_', ' ').toUpperCase()}
                        </div>
                        <span className="dup-sim-badge">{d.similarity_percentage}% SIMILARITY</span>
                      </div>
                      <div className="dup-locations">
                        <code>{d.primary_location.filename}:{d.primary_location.line_start}-{d.primary_location.line_end}</code>
                        <span>&nbsp;→&nbsp;</span>
                        <code>{d.duplicate_location.filename}:{d.duplicate_location.line_start}-{d.duplicate_location.line_end}</code>
                      </div>
                      <p className="dup-rec">{d.recommendation}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="clean-state-box">
                  <ShieldCheck size={16} className="text-success" />
                  <span>Zero code duplications detected across this project.</span>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Architecture Recommendations */}
          {activeTab === 'recommendations' && (
            <div className="dashboard-panel">
              <ul className="recs-list">
                {projectResult.recommendations.map((rec, idx) => (
                  <li key={idx} className="rec-item">
                    <span className="rec-bullet">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
