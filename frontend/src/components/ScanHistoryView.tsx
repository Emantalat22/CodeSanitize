import React, { useEffect, useState } from 'react';
import {
  History,
  FileText,
  Download,
  Trash2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

import { ScanHistorySummary } from '../types';

export const ScanHistoryView: React.FC = () => {
  const [history, setHistory] = useState<ScanHistorySummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/history?limit=50');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan history');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteScan = async (scanId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/history/${scanId}`, { method: 'DELETE' });
      if (res.ok) {
        setHistory((prev) => prev.filter((item) => item.scan_id !== scanId));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Clear all local scan history records?')) return;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/history', { method: 'DELETE' });
      if (res.ok) {
        setHistory([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <div className="scan-history-container">
      <div className="history-header-card">
        <div className="history-title-group">
          <History size={22} className="text-primary" />
          <div>
            <h3 className="history-title">Persistent Scan History</h3>
            <p className="history-subtitle">
              Local persistent storage of single-file and project static intelligence scans.
            </p>
          </div>
        </div>

        <div className="history-actions">
          <button
            type="button"
            onClick={fetchHistory}
            disabled={loading}
            className="export-btn btn-json"
          >
            <RefreshCw size={13} className={loading ? 'icon-spin' : ''} />
            <span>Refresh</span>
          </button>

          {history.length > 0 && (
            <button
              type="button"
              onClick={handleClearHistory}
              className="export-btn btn-clear"
              title="Clear all records"
            >
              <Trash2 size={13} />
              <span>Clear All</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={16} className="text-error" />
          <span>{error}</span>
        </div>
      )}

      {history.length > 0 ? (
        <div className="dashboard-panel">
          <div className="findings-table-wrapper">
            <table className="findings-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Target / Name</th>
                  <th>Type</th>
                  <th>Language</th>
                  <th>LOC</th>
                  <th>Score</th>
                  <th>Findings</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((scan) => (
                  <tr key={scan.scan_id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '12px', color: '#94a3b8' }}>
                      {scan.timestamp ? scan.timestamp.slice(0, 19).replace('T', ' ') : 'N/A'}
                    </td>
                    <td>
                      <strong>{scan.target_name}</strong>
                    </td>
                    <td>
                      <span className={`type-badge ${scan.scan_type === 'project' ? 'project' : 'file'}`}>
                        {scan.scan_type.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className="lang-pill">{scan.language.toUpperCase()}</span>
                    </td>
                    <td>{scan.lines_of_code}</td>
                    <td>
                      <span
                        className={
                          scan.score >= 80 ? 'text-success' : scan.score >= 60 ? 'text-warning' : 'text-error'
                        }
                      >
                        <strong>{scan.score}</strong>/100
                      </span>
                    </td>
                    <td>
                      {scan.critical_security_count > 0 ? (
                        <span className="text-error">{scan.critical_security_count} Critical</span>
                      ) : (
                        <span className="text-muted">{scan.findings_count} Total</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div className="history-row-actions">
                        <a
                          href={`http://127.0.0.1:8000/api/reports/${scan.scan_id}/html`}
                          target="_blank"
                          rel="noreferrer"
                          className="action-icon-link"
                          title="Open HTML Report"
                        >
                          <FileText size={14} />
                        </a>
                        <a
                          href={`http://127.0.0.1:8000/api/reports/${scan.scan_id}/json`}
                          target="_blank"
                          rel="noreferrer"
                          className="action-icon-link"
                          title="Download JSON Telemetry"
                        >
                          <Download size={14} />
                        </a>
                        <button
                          type="button"
                          onClick={() => handleDeleteScan(scan.scan_id)}
                          className="action-icon-btn delete-btn"
                          title="Delete from history"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        !loading && (
          <div className="clean-state-box">
            <History size={20} className="text-muted" />
            <span>No previous scans stored in local history yet. Run an analysis to persist.</span>
          </div>
        )
      )}
    </div>
  );
};
