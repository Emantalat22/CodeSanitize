import React from 'react';
import { BarChart3, ShieldAlert, Layers } from 'lucide-react';
import { AnalysisFinding, ComplexityMetrics, StructuralMetrics } from '../types';


interface VisualAnalyticsProps {
  complexityMetrics: ComplexityMetrics;
  structuralMetrics: StructuralMetrics;
  findings: AnalysisFinding[];
}

export const VisualAnalytics: React.FC<VisualAnalyticsProps> = ({
  complexityMetrics,
  structuralMetrics,
  findings,
}) => {
  // 1. Complexity Distribution
  const fnComplexities = complexityMetrics.function_complexities || [];
  const simpleCount = fnComplexities.filter((f) => f.cyclomatic_complexity <= 5).length;
  const modCount = fnComplexities.filter((f) => f.cyclomatic_complexity > 5 && f.cyclomatic_complexity <= 12).length;
  const highCount = fnComplexities.filter((f) => f.cyclomatic_complexity > 12).length;
  const totalFns = Math.max(fnComplexities.length, 1);

  const simplePct = Math.round((simpleCount / totalFns) * 100);
  const modPct = Math.round((modCount / totalFns) * 100);
  const highPct = Math.round((highCount / totalFns) * 100);

  // 2. Risk & Severity Distribution
  const critCount = findings.filter((f) => f.severity === 'critical').length;
  const highRiskCount = findings.filter((f) => f.severity === 'high').length;
  const medRiskCount = findings.filter((f) => f.severity === 'medium').length;
  const lowRiskCount = findings.filter((f) => f.severity === 'low' || f.severity === 'info').length;
  const totalFindings = Math.max(findings.length, 1);

  const critPct = findings.length > 0 ? Math.round((critCount / totalFindings) * 100) : 0;
  const highRiskPct = findings.length > 0 ? Math.round((highRiskCount / totalFindings) * 100) : 0;
  const medRiskPct = findings.length > 0 ? Math.round((medRiskCount / totalFindings) * 100) : 0;
  const lowRiskPct = findings.length > 0 ? Math.round((lowRiskCount / totalFindings) * 100) : 0;

  // 3. Code Structure Composition
  const fnCount = structuralMetrics.function_count || 0;
  const clsCount = structuralMetrics.class_count || 0;
  const impCount = structuralMetrics.import_count || 0;
  const docCount = (structuralMetrics.docstring_count ?? 0) + (structuralMetrics.comment_count ?? 0);
  const totalStruct = fnCount + clsCount + impCount + docCount;
  const fnPct = totalStruct > 0 ? Math.round((fnCount / totalStruct) * 100) : 40;
  const clsPct = totalStruct > 0 ? Math.round((clsCount / totalStruct) * 100) : 20;
  const impPct = totalStruct > 0 ? Math.round((impCount / totalStruct) * 100) : 20;
  const docPct = totalStruct > 0 ? Math.round((docCount / totalStruct) * 100) : 20;

  return (
    <div className="dashboard-panel visual-analytics-panel">
      <div className="panel-header">
        <div className="panel-title-group">
          <BarChart3 size={16} className="text-accent" />
          <h4 className="panel-title">Visual Code Analytics & Risk Distribution</h4>
        </div>
        <span className="panel-subtitle">Multi-dimensional structural and security telemetry</span>
      </div>

      <div className="analytics-charts-grid">
        {/* Chart 1: Complexity Distribution Bar */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-icon">
              <BarChart3 size={14} className="text-primary" />
              <span className="chart-name">Function Complexity Breakdown</span>
            </div>
            <span className="chart-badge">{fnComplexities.length} Functions</span>
          </div>

          <div className="chart-body">
            <div className="multi-bar-track">
              {simplePct > 0 && (
                <div
                  className="bar-seg seg-simple"
                  style={{ width: `${Math.max(simplePct, 8)}%` }}
                  title={`Simple Complexity (<=5): ${simpleCount} (${simplePct}%)`}
                >
                  {simplePct >= 12 && `${simplePct}%`}
                </div>
              )}
              {modPct > 0 && (
                <div
                  className="bar-seg seg-moderate"
                  style={{ width: `${Math.max(modPct, 8)}%` }}
                  title={`Moderate Complexity (6-12): ${modCount} (${modPct}%)`}
                >
                  {modPct >= 12 && `${modPct}%`}
                </div>
              )}
              {highPct > 0 && (
                <div
                  className="bar-seg seg-complex"
                  style={{ width: `${Math.max(highPct, 8)}%` }}
                  title={`High Complexity (>12): ${highCount} (${highPct}%)`}
                >
                  {highPct >= 12 && `${highPct}%`}
                </div>
              )}
              {fnComplexities.length === 0 && (
                <div className="bar-seg seg-simple" style={{ width: '100%' }}>
                  100% (Module)
                </div>
              )}
            </div>

            <div className="chart-legend-grid">
              <div className="legend-row">
                <span className="legend-dot dot-simple"></span>
                <span className="l-name">Simple (&le; 5)</span>
                <span className="l-val">{simpleCount}</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot dot-moderate"></span>
                <span className="l-name">Moderate (6–12)</span>
                <span className="l-val">{modCount}</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot dot-complex"></span>
                <span className="l-name">High (&gt; 12)</span>
                <span className="l-val">{highCount}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart 2: Code Structure Composition */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-icon">
              <Layers size={14} className="text-accent" />
              <span className="chart-name">Structural Composition</span>
            </div>
            <span className="chart-badge">{structuralMetrics.lines_of_code} LOC</span>
          </div>

          <div className="chart-body">
            <div className="multi-bar-track">
              {fnPct > 0 && (
                <div
                  className="bar-seg seg-fn"
                  style={{ width: `${Math.max(fnPct, 8)}%` }}
                  title={`Functions: ${structuralMetrics.function_count} (${fnPct}%)`}
                >
                  {fnPct >= 12 && `Fns`}
                </div>
              )}
              {clsPct > 0 && (
                <div
                  className="bar-seg seg-cls"
                  style={{ width: `${Math.max(clsPct, 8)}%` }}
                  title={`Classes: ${structuralMetrics.class_count} (${clsPct}%)`}
                >
                  {clsPct >= 12 && `Cls`}
                </div>
              )}
              {impPct > 0 && (
                <div
                  className="bar-seg seg-imp"
                  style={{ width: `${Math.max(impPct, 8)}%` }}
                  title={`Imports: ${structuralMetrics.import_count} (${impPct}%)`}
                >
                  {impPct >= 12 && `Imp`}
                </div>
              )}
              {docPct > 0 && (
                <div
                  className="bar-seg seg-doc"
                  style={{ width: `${Math.max(docPct, 8)}%` }}
                  title={`Documentation: ${(((structuralMetrics.comment_ratio ?? 0)) * 100).toFixed(1)}%`}
                >
                  {docPct >= 12 && `Docs`}
                </div>

              )}
            </div>

            <div className="chart-legend-grid">
              <div className="legend-row">
                <span className="legend-dot dot-fn"></span>
                <span className="l-name">Functions</span>
                <span className="l-val">{structuralMetrics.function_count}</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot dot-cls"></span>
                <span className="l-name">Classes</span>
                <span className="l-val">{structuralMetrics.class_count}</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot dot-imp"></span>
                <span className="l-name">Imports</span>
                <span className="l-val">{structuralMetrics.import_count}</span>
              </div>
              <div className="legend-row">
                <span className="legend-dot dot-doc"></span>
                <span className="l-name">Docstrings / Comments</span>
                <span className="l-val">{docPct}% ({Math.round((structuralMetrics.comment_ratio ?? 0) * 100)}% ratio)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart 3: Risk & Findings Distribution */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-icon">
              <ShieldAlert size={14} className="text-warning" />
              <span className="chart-name">Security & Findings Distribution</span>
            </div>
            <span className="chart-badge">{totalFindings} Total Finding(s)</span>
          </div>

          <div className="multi-bar-track">
            {totalFindings === 0 ? (
              <div className="bar-seg seg-clean" style={{ width: '100%' }}>
                CLEAN (0 ISSUES)
              </div>
            ) : (
              <>
                {critPct > 0 && (
                  <div className="bar-seg seg-crit" style={{ width: `${critPct}%` }} title={`Critical: ${critPct}%`}>
                    {critPct}%
                  </div>
                )}
                {highRiskPct > 0 && (
                  <div className="bar-seg seg-high-risk" style={{ width: `${highRiskPct}%` }} title={`High: ${highRiskPct}%`}>
                    {highRiskPct}%
                  </div>
                )}
                {medRiskPct > 0 && (
                  <div className="bar-seg seg-med-risk" style={{ width: `${medRiskPct}%` }} title={`Medium: ${medRiskPct}%`}>
                    {medRiskPct}%
                  </div>
                )}
                {lowRiskPct > 0 && (
                  <div className="bar-seg seg-low-risk" style={{ width: `${lowRiskPct}%` }} title={`Low/Info: ${lowRiskPct}%`}>
                    {lowRiskPct}%
                  </div>
                )}
              </>
            )}
          </div>

          <div className="chart-legend-grid">
            <div className="legend-row">
              <span className="legend-dot dot-crit"></span>
              <span className="l-name">Critical Severity</span>
              <span className="l-val">{critCount} ({critPct}%)</span>
            </div>
            <div className="legend-row">
              <span className="legend-dot dot-high-risk"></span>
              <span className="l-name">High Severity</span>
              <span className="l-val">{highRiskCount} ({highRiskPct}%)</span>
            </div>
            <div className="legend-row">
              <span className="legend-dot dot-med-risk"></span>
              <span className="l-name">Medium Severity</span>
              <span className="l-val">{medRiskCount} ({medRiskPct}%)</span>
            </div>
            <div className="legend-row">
              <span className="legend-dot dot-low-risk"></span>
              <span className="l-name">Low / Informational</span>
              <span className="l-val">{lowRiskCount} ({lowRiskPct}%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
