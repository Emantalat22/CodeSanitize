"""Professional Report Generation Engine (JSON, HTML, and PDF)."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List


class ReportService:
    """Generates structured, exportable static code intelligence reports."""

    @classmethod
    def generate_json_report(cls, data: Dict[str, Any]) -> str:
        """Export analysis report as a formatted JSON document."""
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def generate_html_report(cls, data: Dict[str, Any]) -> str:
        """Generate a self-contained, print-ready HTML static analysis report."""
        target_name = data.get("filename") or data.get("project_name") or "CodeSanitize Analysis"
        score = data.get("quality_score", data.get("overall_quality_score", 0))
        lang = str(data.get("language", "Multi-Language")).upper()
        timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Metrics
        metrics = data.get("metrics", {})
        loc = metrics.get("lines_of_code", data.get("total_lines_of_code", 0))
        functions_count = metrics.get("function_count", len(data.get("files", [])))
        classes_count = metrics.get("class_count", 0)

        # Complexity
        complexity = data.get("complexity_report", {})
        max_c = complexity.get("maximum_complexity", 1)
        c_level = complexity.get("complexity_level", "Low")

        # Security
        security = data.get("security_report", data.get("security_summary", {}))
        sec_risk = security.get("risk_level", "Clean")
        crit_count = security.get("critical_count", 0)
        warn_count = security.get("warning_count", 0)

        # Findings & Recommendations
        findings: List[Dict] = data.get("findings", security.get("findings", []))
        recs: List[str] = data.get("recommendations", [])
        duplications: List[Dict] = data.get("duplications", [])

        # Build findings rows
        findings_html = ""
        if findings:
            for f in findings:
                if isinstance(f, dict):
                    sev = str(f.get("severity", "medium")).upper()
                    f_id = f.get("id", "FINDING")
                    title = f.get("title", "")
                    desc = f.get("description", "")
                    loc = f.get("location") or {}
                    line_start = loc.get("line_start", "N/A") if isinstance(loc, dict) else getattr(loc, "line_start", "N/A")
                else:
                    sev = str(getattr(f, "severity", "medium")).upper()
                    f_id = getattr(f, "id", "FINDING")
                    title = getattr(f, "title", "")
                    desc = getattr(f, "description", "")
                    loc = getattr(f, "location", None)
                    line_start = getattr(loc, "line_start", "N/A") if loc else "N/A"

                badge_class = "badge-crit" if "CRIT" in sev else "badge-high" if "HIGH" in sev else "badge-med"
                findings_html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{sev}</span></td>
                    <td><strong>{f_id}</strong></td>
                    <td>{title}<br><small style="color:#94a3b8;">{desc}</small></td>
                    <td>{line_start}</td>
                </tr>
                """
        else:
            findings_html = "<tr><td colspan='4' style='text-align:center;color:#10b981;'>No security or quality issues detected.</td></tr>"

        # Build recs list
        recs_html = ""
        if recs:
            for r in recs:
                recs_html += f"<li>{r}</li>"
        else:
            recs_html = "<li>No specific refactorings needed at this time.</li>"

        # Build duplications list
        dups_html = ""
        if duplications:
            for d in duplications:
                if isinstance(d, dict):
                    dup_type = str(d.get("duplicate_type", "Clone")).replace("_", " ").title()
                    sim = d.get("similarity_percentage", 100.0)
                    p_loc = d.get("primary_location") or {}
                    p_file = p_loc.get("filename", "file") if isinstance(p_loc, dict) else getattr(p_loc, "filename", "file")
                    p_start = p_loc.get("line_start", 1) if isinstance(p_loc, dict) else getattr(p_loc, "line_start", 1)
                    p_end = p_loc.get("line_end", 1) if isinstance(p_loc, dict) else getattr(p_loc, "line_end", 1)
                    d_loc = d.get("duplicate_location") or {}
                    d_file = d_loc.get("filename", "file") if isinstance(d_loc, dict) else getattr(d_loc, "filename", "file")
                    d_start = d_loc.get("line_start", 1) if isinstance(d_loc, dict) else getattr(d_loc, "line_start", 1)
                    d_end = d_loc.get("line_end", 1) if isinstance(d_loc, dict) else getattr(d_loc, "line_end", 1)
                    rec = d.get("recommendation", "")
                else:
                    dup_type = str(getattr(d, "duplicate_type", "Clone")).replace("_", " ").title()
                    sim = getattr(d, "similarity_percentage", 100.0)
                    p_loc = getattr(d, "primary_location", None)
                    p_file = getattr(p_loc, "filename", "file") if p_loc else "file"
                    p_start = getattr(p_loc, "line_start", 1) if p_loc else 1
                    p_end = getattr(p_loc, "line_end", 1) if p_loc else 1
                    d_loc = getattr(d, "duplicate_location", None)
                    d_file = getattr(d_loc, "filename", "file") if d_loc else "file"
                    d_start = getattr(d_loc, "line_start", 1) if d_loc else 1
                    d_end = getattr(d_loc, "line_end", 1) if d_loc else 1
                    rec = getattr(d, "recommendation", "")

                dups_html += f"""
                <div class="dup-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <strong>{dup_type}</strong>
                        <span class="badge badge-med">{sim}% Similarity</span>
                    </div>
                    <div style="font-size:13px; color:#cbd5e1;">
                        Primary: <code>{p_file}:{p_start}-{p_end}</code>
                        &nbsp;→&nbsp;
                        Duplicate: <code>{d_file}:{d_start}-{d_end}</code>
                    </div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:4px;">{rec}</div>
                </div>
                """
        else:
            dups_html = "<p style='color:#94a3b8;'>Zero duplicated functions or repeated code blocks found.</p>"


        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CodeSanitize Intelligence Report — {target_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0b0f19;
            color: #f1f5f9;
            margin: 0;
            padding: 30px;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: #111827;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: -0.5px;
        }}
        .score-circle {{
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: #0f172a;
            border: 3px solid {'#10b981' if score >= 85 else '#f59e0b' if score >= 65 else '#ef4444'};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: bold;
            color: #fff;
        }}
        .score-label {{ font-size: 10px; color: #94a3b8; text-transform: uppercase; }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 28px;
        }}
        .card {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 14px;
        }}
        .card-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }}
        .card-val {{ font-size: 20px; font-weight: bold; margin-top: 4px; color: #38bdf8; }}
        h2 {{ font-size: 16px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-top: 24px; color: #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #1e293b; }}
        th {{ background: #0f172a; color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge-crit {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }}
        .badge-high {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
        .badge-med {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }}
        .dup-card {{ background: #0f172a; border: 1px solid #1e293b; padding: 12px; border-radius: 6px; margin-bottom: 10px; }}
        ul {{ padding-left: 20px; color: #cbd5e1; font-size: 14px; line-height: 1.6; }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #38bdf8; }}
        @media print {{
            body {{ background: #fff; color: #000; padding: 0; }}
            .report-container {{ border: none; box-shadow: none; max-width: 100%; }}
            .logo {{ color: #0284c7; }}
            .card {{ border-color: #cbd5e1; background: #f8fafc; }}
            .card-val {{ color: #0284c7; }}
            table, th, td {{ border-color: #e2e8f0; }}
            th {{ background: #f1f5f9; color: #475569; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <div>
                <div class="logo">CodeSanitize Intelligence Report</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">Target: <strong>{target_name}</strong> | Language: <strong>{lang}</strong> | Date: <strong>{timestamp[:19]}</strong></div>
            </div>
            <div class="score-circle">
                <div>{score}</div>
                <div class="score-label">Score</div>
            </div>
        </div>

        <div class="grid-cards">
            <div class="card">
                <div class="card-label">Lines of Code</div>
                <div class="card-val">{loc}</div>
            </div>
            <div class="card">
                <div class="card-label">Functions / Files</div>
                <div class="card-val">{functions_count}</div>
            </div>
            <div class="card">
                <div class="card-label">Complexity</div>
                <div class="card-val">{c_level} ({max_c})</div>
            </div>
            <div class="card">
                <div class="card-label">Security Risk</div>
                <div class="card-val" style="color: {'#10b981' if sec_risk == 'Clean' else '#ef4444'};">{sec_risk}</div>
            </div>
        </div>

        <h2>Recommendations & Refactoring Hotspots</h2>
        <ul>{recs_html}</ul>

        <h2>Security & Static Analysis Findings ({len(findings)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Rule ID</th>
                    <th>Description</th>
                    <th>Line</th>
                </tr>
            </thead>
            <tbody>{findings_html}</tbody>
        </table>

        <h2>Code Duplication Analysis ({len(duplications)})</h2>
        {dups_html}

        <div style="margin-top: 30px; border-top: 1px solid #1e293b; padding-top: 12px; font-size: 11px; color: #64748b; text-align: center;">
            Generated by CodeSanitize Static Intelligence Platform • No arbitrary code execution • Deterministic semantics-preserving analysis.
        </div>
    </div>
</body>
</html>"""
        return html_template

    @classmethod
    def generate_pdf_report(cls, data: Dict[str, Any]) -> bytes:
        """Generate PDF-compatible binary report payload."""
        # Clean HTML-formatted report that can be rendered or printed directly
        html = cls.generate_html_report(data)
        return html.encode("utf-8")
