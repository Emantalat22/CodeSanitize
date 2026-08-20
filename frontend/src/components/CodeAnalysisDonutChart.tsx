import React from 'react';
import { AnalysisFinding, CodeMetrics, ComplexityMetrics, ComplexityReport, StructuralMetrics } from '../types';

interface CodeAnalysisDonutChartProps {
  overallScore: number;
  complexityMetrics: ComplexityMetrics | ComplexityReport;
  structuralMetrics: StructuralMetrics | CodeMetrics;
  findings: AnalysisFinding[];
}

export const CodeAnalysisDonutChart: React.FC<CodeAnalysisDonutChartProps> = ({
  overallScore,
  complexityMetrics,
  structuralMetrics,
  findings,
}) => {
  // 1. Maintainability Dimension Score (0 - 100)
  const docRatio = structuralMetrics.comment_ratio ?? 0;
  const avgLen = structuralMetrics.average_function_length ?? 0;

  let maintainabilityScore = 88;
  if (docRatio >= 0.15) maintainabilityScore += 8;
  else if (docRatio < 0.05) maintainabilityScore -= 12;
  if (avgLen > 40) maintainabilityScore -= 15;
  else if (avgLen > 25) maintainabilityScore -= 8;
  maintainabilityScore = Math.max(Math.min(maintainabilityScore, 100), 25);

  // 2. Complexity Dimension Score (0 - 100)
  const cyclomatic = complexityMetrics.cyclomatic_complexity;
  const nesting = complexityMetrics.max_nesting_depth;
  let complexityScore = 90;
  if (cyclomatic > 15) complexityScore -= 28;
  else if (cyclomatic > 8) complexityScore -= 14;
  else if (cyclomatic > 4) complexityScore -= 5;
  if (nesting > 4) complexityScore -= (nesting - 4) * 8;
  complexityScore = Math.max(Math.min(complexityScore, 100), 20);

  // 3. Security Dimension Score (0 - 100)
  const secFindings = findings.filter((f) => f.category === 'security');
  let securityScore = 100;
  for (const f of secFindings) {
    if (f.severity === 'critical') securityScore -= 35;
    else if (f.severity === 'high') securityScore -= 20;
    else if (f.severity === 'medium') securityScore -= 10;
    else securityScore -= 5;
  }
  securityScore = Math.max(Math.min(securityScore, 100), 15);

  // 4. Structure Dimension Score (0 - 100)
  let structureScore = 88;
  if (structuralMetrics.lines_of_code > 0) {
    if (structuralMetrics.function_count > 0 || structuralMetrics.class_count > 0) {
      structureScore = 94;
    }
  }
  structureScore = Math.max(Math.min(structureScore, 100), 30);

  // Weights and categories
  const categories = [
    {
      name: 'Maintainability',
      score: maintainabilityScore,
      color: '#38bdf8', // Cyan
      desc: 'Docstrings, comment ratio & function length',
    },
    {
      name: 'Complexity',
      score: complexityScore,
      color: '#818cf8', // Indigo
      desc: 'McCabe cyclomatic flow & nesting depth',
    },
    {
      name: 'Security',
      score: securityScore,
      color: securityScore >= 80 ? '#34d399' : securityScore >= 60 ? '#fbbf24' : '#fb7185', // Emerald/Amber/Rose
      desc: 'Static pattern scan & vulnerability safety',
    },
    {
      name: 'Structure',
      score: structureScore,
      color: '#60a5fa', // Blue
      desc: 'AST hierarchy, interfaces & modularity',
    },
  ];

  // Proportional Donut Calculation
  const totalPoints = categories.reduce((sum, c) => sum + c.score, 0);
  const radius = 56;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius; // ≈ 351.86

  let accumulatedPercent = 0;
  const slices = categories.map((cat) => {
    const percent = totalPoints > 0 ? (cat.score / totalPoints) * 100 : 25;
    const strokeDasharray = `${(percent / 100) * circumference} ${circumference}`;
    const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
    accumulatedPercent += percent;
    return {
      ...cat,
      percent: Math.round(percent),
      strokeDasharray,
      strokeDashoffset,
    };
  });

  const getScoreGrade = (score: number) => {
    if (score >= 85) return { grade: 'A', label: 'OPTIMAL', color: 'text-success' };
    if (score >= 70) return { grade: 'B', label: 'GOOD', color: 'text-good' };
    if (score >= 50) return { grade: 'C', label: 'MODERATE', color: 'text-warning' };
    return { grade: 'D', label: 'ATTENTION', color: 'text-error' };
  };

  const status = getScoreGrade(overallScore);

  return (
    <div className="donut-analytics-card">
      {/* 1. Left: Single SVG Donut Chart */}
      <div className="donut-chart-container">
        <svg className="donut-svg" width="148" height="148" viewBox="0 0 148 148">
          {/* Background Track Circle */}
          <circle
            cx="74"
            cy="74"
            r={radius}
            fill="transparent"
            stroke="#162035"
            strokeWidth={strokeWidth}
          />
          {/* Segment Arcs */}
          {slices.map((slice) => (
            <circle
              key={slice.name}
              cx="74"
              cy="74"
              r={radius}
              fill="transparent"
              stroke={slice.color}
              strokeWidth={strokeWidth}
              strokeDasharray={slice.strokeDasharray}
              strokeDashoffset={slice.strokeDashoffset}
              strokeLinecap="butt"
              transform="rotate(-90 74 74)"
              style={{ transition: 'stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease' }}
            />
          ))}
        </svg>

        {/* Donut Center Overall Score */}
        <div className="donut-center-content">
          <span className="donut-score-val">{overallScore}</span>
          <span className="donut-score-sub">/100</span>
          <span className={`donut-score-status ${status.color}`}>{status.label}</span>
        </div>
      </div>

      {/* 2. Right: Category Legend with Percentages & Scores */}
      <div className="donut-legend-list">
        {slices.map((item) => (
          <div key={item.name} className="donut-legend-item">
            <div className="legend-indicator" style={{ backgroundColor: item.color }}></div>
            <div className="legend-info">
              <div className="legend-title-row">
                <span className="legend-title">{item.name}</span>
                <span className="legend-percent-tag">{item.percent}% Distribution</span>
              </div>
              <span className="legend-desc">{item.desc}</span>
            </div>
            <div className="legend-score-col">
              <span className="legend-score-val" style={{ color: item.color }}>
                {item.score}
              </span>
              <span className="legend-score-unit">/100</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
