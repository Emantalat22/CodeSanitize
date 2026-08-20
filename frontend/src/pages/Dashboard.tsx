import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Code2,
  Layers,
  Activity,
  Zap,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { MetricCard } from '../components/MetricCard';
import { ChartCard } from '../components/ChartCard';
import { FindingTable } from '../components/FindingTable';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { analysisResult } = useWorkspace();

  const metrics = analysisResult?.metrics || {
    lines_of_code: 32,
    function_count: 1,
    class_count: 0,
    blank_lines: 4,
    comment_lines: 4,
    import_count: 1,
    average_function_length: 12,
  };
  const qualityScore = analysisResult?.quality_score ?? 88;
  const complexity = analysisResult?.complexity_report?.cyclomatic_complexity ?? 3;
  const securityRisk = analysisResult?.security_report?.risk_level ?? 'low';
  const findings = analysisResult?.findings || [];
  const recommendations = analysisResult?.recommendations || [
    'Run static analysis on your code to identify security vulnerabilities, high complexity, and style regularities.',
  ];

  const getScoreBadge = (score: number) => {
    if (score >= 85) return { text: 'GRADE A', variant: 'success' as const };
    if (score >= 70) return { text: 'GRADE B', variant: 'info' as const };
    if (score >= 50) return { text: 'GRADE C', variant: 'warning' as const };
    return { text: 'GRADE F', variant: 'error' as const };
  };

  const getRiskBadge = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'critical':
      case 'high':
        return { text: 'HIGH RISK', variant: 'error' as const };
      case 'medium':
        return { text: 'MODERATE', variant: 'warning' as const };
      case 'low':
      default:
        return { text: 'LOW RISK', variant: 'success' as const };
    }
  };

  return (
    <div className="page-dashboard-container">
      {/* 1. Dashboard Welcome & Overview Cards */}
      <div className="dashboard-grid-cards">
        <MetricCard
          label="Code Quality Score"
          value={`${qualityScore}/100`}
          subtext="Static maintainability & AST rating"
          badge={getScoreBadge(qualityScore)}
          valueColor={qualityScore >= 80 ? '#10b981' : qualityScore >= 60 ? '#38bdf8' : '#f59e0b'}
          icon={<ShieldCheck size={16} className="text-teal" />}
          onClick={() => navigate('/analyze')}
        />

        <MetricCard
          label="Lines of Code"
          value={metrics.lines_of_code}
          subtext="Physical executable code lines"
          icon={<Code2 size={16} className="text-primary" />}
        />

        <MetricCard
          label="Functions Count"
          value={metrics.function_count}
          subtext="Declared methods & functions"
          icon={<Zap size={16} className="text-purple" />}
        />

        <MetricCard
          label="Class Count"
          value={metrics.class_count}
          subtext="Object-oriented definitions"
          icon={<Layers size={16} className="text-muted" />}
        />


        <MetricCard
          label="Complexity Score"
          value={complexity}
          subtext="McCabe cyclomatic paths"
          badge={{
            text: complexity <= 5 ? 'OPTIMAL' : complexity <= 10 ? 'MODERATE' : 'COMPLEX',
            variant: complexity <= 5 ? 'success' : complexity <= 10 ? 'info' : 'warning',
          }}
          icon={<Activity size={16} className="text-warning" />}
        />

        <MetricCard
          label="Security Risk Level"
          value={securityRisk.toUpperCase()}
          subtext={`${findings.length} detected security issues`}
          badge={getRiskBadge(securityRisk)}
          valueColor={securityRisk === 'low' ? '#10b981' : securityRisk === 'medium' ? '#f59e0b' : '#f43f5e'}
          icon={<ShieldAlert size={16} className="text-error" />}
          onClick={() => navigate('/security')}
        />
      </div>

      {/* 2. Visual Analytics Section (Single Donut Chart) + Recommendations */}
      <div className="dashboard-analytics-row">
        {/* Visual Code Health Distribution Chart */}
        <div className="analytics-chart-col">
          <ChartCard result={analysisResult} />
        </div>

        {/* Actionable Static Intelligence Recommendations */}
        <div className="analytics-recs-col">
          <div className="card-pro-panel">
            <div className="card-pro-header">
              <div className="card-header-left">
                <Sparkles size={15} className="text-purple" />
                <h4>Static Intelligence Recommendations</h4>
              </div>
              <button
                type="button"
                onClick={() => navigate('/transform')}
                className="btn-link-action"
              >
                <span>Normalize Code</span>
                <ArrowRight size={13} />
              </button>
            </div>

            <ul className="recs-list-pro">
              {recommendations.map((rec, idx) => (
                <li key={idx} className="rec-item-pro">
                  <span className="rec-bullet-pro">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* 3. Findings Section */}
      <div className="dashboard-findings-panel">
        <div className="card-pro-header">
          <div className="card-header-left">
            <ShieldAlert size={15} className="text-teal" />
            <h4>Static Security Findings & Vulnerability Signals ({findings.length})</h4>
          </div>
          <button
            type="button"
            onClick={() => navigate('/security')}
            className="btn-link-action"
          >
            <span>View Full Security Report</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <FindingTable
          findings={findings}
          emptyMessage="No security vulnerabilities or risky API invocations detected in the current code buffer."
        />
      </div>
    </div>
  );
};
