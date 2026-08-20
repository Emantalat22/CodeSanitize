import React from 'react';
import { PieChart } from 'lucide-react';
import { AnalysisResult } from '../types';

interface ChartCardProps {
  result?: AnalysisResult | null;
}

export const ChartCard: React.FC<ChartCardProps> = ({ result }) => {
  const qualityScore = result ? result.quality_score : 88;
  const complexity = result ? result.complexity_report?.cyclomatic_complexity || 4 : 4;
  const securityRisk = result ? result.security_report?.risk_level || 'low' : 'low';

  // Compute 4 normalized components of code health distribution
  const maintainabilityPct = Math.max(15, Math.min(45, Math.round((qualityScore / 100) * 35)));
  const complexityPct = Math.max(10, Math.min(30, Math.round(complexity > 15 ? 30 : complexity > 8 ? 24 : 16)));
  const securityPct = Math.max(
    10,
    Math.min(35, securityRisk === 'critical' ? 35 : securityRisk === 'high' ? 28 : securityRisk === 'medium' ? 20 : 14)
  );
  const structurePct = Math.max(10, 100 - (maintainabilityPct + complexityPct + securityPct));


  const total = maintainabilityPct + complexityPct + securityPct + structurePct;
  const normM = (maintainabilityPct / total) * 100;
  const normC = (complexityPct / total) * 100;
  const normS = (securityPct / total) * 100;
  const normSt = (structurePct / total) * 100;

  const radius = 50;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;

  const arc1Len = (normM / 100) * circumference;
  const arc2Len = (normC / 100) * circumference;
  const arc3Len = (normS / 100) * circumference;
  const arc4Len = (normSt / 100) * circumference;

  const arc1Offset = 0;
  const arc2Offset = -arc1Len;
  const arc3Offset = -(arc1Len + arc2Len);
  const arc4Offset = -(arc1Len + arc2Len + arc3Len);

  return (
    <div className="chart-card-pro">
      <div className="card-pro-header">
        <div className="card-header-left">
          <PieChart size={15} className="text-teal" />
          <h4>Code Health Distribution</h4>
        </div>
        <span className="card-header-tag">Static AST Profiling</span>
      </div>

      <div className="donut-chart-layout">
        {/* SVG Donut */}
        <div className="donut-visual-box">
          <svg width="140" height="140" viewBox="0 0 140 140" className="donut-svg">
            <g transform="rotate(-90 70 70)">
              {/* Background ring */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke="#111827"
                strokeWidth={strokeWidth}
              />
              {/* Arc 1: Maintainability (Electric Blue) */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke="#06b6d4"
                strokeWidth={strokeWidth}
                strokeDasharray={`${arc1Len} ${circumference - arc1Len}`}
                strokeDashoffset={arc1Offset}
                strokeLinecap="round"
              />
              {/* Arc 2: Complexity (Soft Purple) */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke="#818cf8"
                strokeWidth={strokeWidth}
                strokeDasharray={`${arc2Len} ${circumference - arc2Len}`}
                strokeDashoffset={arc2Offset}
              />
              {/* Arc 3: Security (Emerald) */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke="#10b981"
                strokeWidth={strokeWidth}
                strokeDasharray={`${arc3Len} ${circumference - arc3Len}`}
                strokeDashoffset={arc3Offset}
              />
              {/* Arc 4: Structure (Indigo/Slate) */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke="#64748b"
                strokeWidth={strokeWidth}
                strokeDasharray={`${arc4Len} ${circumference - arc4Len}`}
                strokeDashoffset={arc4Offset}
              />
            </g>
          </svg>

          <div className="donut-center-telemetry">
            <span className="donut-score-text">{qualityScore}</span>
            <span className="donut-sub-text">SCORE</span>
          </div>
        </div>

        {/* Legend */}
        <div className="donut-legend-pro">
          <div className="legend-row-pro">
            <span className="legend-indicator" style={{ background: '#06b6d4' }}></span>
            <span className="legend-title">Maintainability</span>
            <span className="legend-val">{Math.round(normM)}%</span>
          </div>

          <div className="legend-row-pro">
            <span className="legend-indicator" style={{ background: '#818cf8' }}></span>
            <span className="legend-title">Complexity</span>
            <span className="legend-val">{Math.round(normC)}%</span>
          </div>

          <div className="legend-row-pro">
            <span className="legend-indicator" style={{ background: '#10b981' }}></span>
            <span className="legend-title">Security</span>
            <span className="legend-val">{Math.round(normS)}%</span>
          </div>

          <div className="legend-row-pro">
            <span className="legend-indicator" style={{ background: '#64748b' }}></span>
            <span className="legend-title">Structure</span>
            <span className="legend-val">{Math.round(normSt)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
