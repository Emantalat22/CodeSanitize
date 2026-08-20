import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, Info } from 'lucide-react';
import { AnalysisFinding } from '../types';

interface FindingTableProps {
  findings: AnalysisFinding[];
  emptyMessage?: string;
}

export const FindingTable: React.FC<FindingTableProps> = ({
  findings = [],
  emptyMessage = 'No findings detected.',
}) => {
  if (!findings || findings.length === 0) {
    return (
      <div className="clean-state-box">
        <ShieldCheck size={16} className="text-success" />
        <span>{emptyMessage}</span>
      </div>
    );
  }

  const getSeverityIcon = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
      case 'high':
        return <ShieldAlert size={13} className="text-error" />;
      case 'medium':
        return <AlertTriangle size={13} className="text-warning" />;
      case 'low':
      case 'info':
      default:
        return <Info size={13} className="text-primary" />;
    }
  };

  return (
    <div className="findings-table-wrapper">
      <table className="findings-table-pro">
        <thead>
          <tr>
            <th style={{ width: '95px' }}>Severity</th>
            <th style={{ width: '220px' }}>Issue & Rule</th>
            <th style={{ width: '80px' }}>Location</th>
            <th>Description & Remediation</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <tr key={f.id} className={`finding-row-pro severity-${f.severity}`}>
              <td>
                <span className={`sev-badge-pro ${f.severity}`}>
                  {getSeverityIcon(f.severity)}
                  <span>{f.severity.toUpperCase()}</span>
                </span>
              </td>
              <td>
                <strong className="finding-title-text">{f.title}</strong>
                <code className="finding-id-tag">{f.id}</code>
              </td>
              <td>
                <span className="location-tag-pro">
                  {f.location?.line_start ? `L${f.location.line_start}` : 'N/A'}
                </span>
              </td>
              <td>
                <p className="finding-desc-p">{f.description}</p>
                {f.recommendation && (
                  <div className="finding-fix-box">
                    <span className="fix-label">Fix:</span>
                    <span className="fix-text">{f.recommendation}</span>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
