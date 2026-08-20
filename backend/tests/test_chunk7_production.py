"""Comprehensive tests for Chunk 7 Production Hardening and Developer Platform Features."""

import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.analyzers.duplication_detector import DuplicationDetector
from app.models.schemas import (
    CodeMetrics,
    ComplexityFunction,
    ComplexityReport,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    ProjectAnalysisRequest,
    ProjectFileInput,
    SecurityReport,
    SupportedLanguage,
)
from app.services.history_service import HistoryService
from app.services.project_service import ProjectAnalysisService
from app.services.recommendation_service import RecommendationService
from app.services.report_service import ReportService


# ===================================================
# 1. Code Duplication Detection Tests
# ===================================================

def test_duplication_detection_identical_functions():
    """Verify duplicate detection finds identical function copies across files."""
    fn_code_a = '''def compute_interest(principal, rate, years):
    interest = principal * rate * years
    total = principal + interest
    return total
'''
    fn_code_b = '''def compute_interest_clone(principal, rate, years):
    interest = principal * rate * years
    total = principal + interest
    return total
'''
    files = [
        ("finance_v1.py", fn_code_a, SupportedLanguage.PYTHON),
        ("finance_v2.py", fn_code_b, SupportedLanguage.PYTHON),
    ]

    dups = DuplicationDetector.detect_duplications_in_files(files)
    assert len(dups) >= 1
    dup = dups[0]
    assert dup.similarity_percentage >= 85.0
    assert "finance_v1.py" in (dup.primary_location.filename, dup.duplicate_location.filename)
    assert "finance_v2.py" in (dup.primary_location.filename, dup.duplicate_location.filename)
    assert "Extract duplicate" in dup.recommendation


def test_duplication_detection_no_duplicates():
    """Verify zero false positive clones for distinct code routines."""
    code_a = '''def calculate_area(r):
    import math
    return math.pi * r * r
'''
    code_b = '''def handle_http_request(req):
    if req.method == "GET":
        return 200
    return 405
'''
    files = [
        ("area.py", code_a, SupportedLanguage.PYTHON),
        ("server.py", code_b, SupportedLanguage.PYTHON),
    ]
    dups = DuplicationDetector.detect_duplications_in_files(files)
    assert len(dups) == 0


# ===================================================
# 2. Recommendation Engine Tests
# ===================================================

def test_recommendation_engine_security_prioritization():
    """Verify security vulnerabilities are prioritized at the top of recommendations."""
    from app.models.schemas import AnalysisFinding

    findings = [
        AnalysisFinding(
            id="SEC-EVAL-01",
            category=FindingCategory.SECURITY,
            severity=FindingSeverity.CRITICAL,
            title="eval execution",
            description="eval used",
            location=FindingLocation(line_start=1),
        ),
        AnalysisFinding(
            id="SEC-SUBPROCESS-SHELL-01",
            category=FindingCategory.SECURITY,
            severity=FindingSeverity.HIGH,
            title="shell=True",
            description="shell command injection",
            location=FindingLocation(line_start=5),
        ),
    ]

    recs = RecommendationService.generate_recommendations(findings=findings)
    assert len(recs) >= 2
    assert any("eval" in r for r in recs)
    assert any("command injection" in r or "shell=False" in r for r in recs)


def test_recommendation_engine_complexity_and_duplication():
    """Verify complexity hotspots and duplications trigger actionable guidance."""
    comp_report = ComplexityReport(
        most_complex_functions=[
            ComplexityFunction(
                name="nested_monster",
                complexity=16,
                risk="high",
                line_start=10,
                nesting_depth=5,
            )
        ]
    )

    recs = RecommendationService.generate_recommendations(
        findings=[],
        complexity=comp_report,
        metrics=CodeMetrics(lines_of_code=100, function_count=1, average_function_length=55.0),
    )

    assert any("nested_monster" in r for r in recs)
    assert any("average 55.0 lines" in r or "decompose oversized" in r for r in recs)


# ===================================================
# 3. Multi-File Project Analysis Tests
# ===================================================

def test_project_analysis_multiple_files(client: TestClient):
    """Verify multi-file project analysis aggregates metrics and language distributions."""
    py_code = '''def add(a, b):
    return a + b
'''
    js_code = '''function multiply(x, y) {
    return x * y;
}
'''
    go_code = '''package main
func Sqr(n int) int {
    return n * n
}
'''
    payload = {
        "project_name": "TestSuiteApp",
        "files": [
            {"filename": "math_utils.py", "code": py_code, "language": "python"},
            {"filename": "calc.js", "code": js_code, "language": "javascript"},
            {"filename": "ops.go", "code": go_code, "language": "go"},
        ],
    }

    res = client.post("/api/project/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["project_name"] == "TestSuiteApp"
    assert data["total_files"] == 3
    assert data["total_lines_of_code"] >= 6
    assert data["overall_quality_score"] > 80
    assert "python" in data["language_distribution"]
    assert "javascript" in data["language_distribution"]
    assert len(data["files"]) == 3


def test_project_analysis_zip_upload(client: TestClient):
    """Verify ZIP file upload extracts, parses, and aggregates multi-file projects."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("src/main.py", "def main():\n    print('hello')\n")
        z.writestr("src/helper.py", "def help_me():\n    return True\n")
        z.writestr("README.md", "# Test Project")

    zip_buffer.seek(0)
    files = {"file": ("test_project.zip", zip_buffer.read(), "application/zip")}

    res = client.post("/api/project/upload?project_name=ZipTestProject", files=files)
    assert res.status_code == 200
    data = res.json()

    assert data["project_name"] == "ZipTestProject"
    assert data["total_files"] >= 2
    assert data["total_lines_of_code"] >= 4


# ===================================================
# 4. Report Generation & Export Tests
# ===================================================

def test_report_generation_json_and_html():
    """Verify ReportService generates structured JSON and standalone HTML reports."""
    sample_data = {
        "filename": "server.py",
        "quality_score": 92,
        "language": "python",
        "metrics": {"lines_of_code": 45, "function_count": 4, "class_count": 1},
        "complexity_report": {"maximum_complexity": 3, "complexity_level": "Low"},
        "security_report": {"risk_level": "Clean", "critical_count": 0, "warning_count": 0},
        "findings": [],
        "recommendations": ["Keep functions focused."],
        "duplications": [],
    }

    json_report = ReportService.generate_json_report(sample_data)
    assert "server.py" in json_report
    assert "92" in json_report

    html_report = ReportService.generate_html_report(sample_data)
    assert "<!DOCTYPE html>" in html_report
    assert "CodeSanitize Intelligence Report" in html_report
    assert "server.py" in html_report


def test_api_report_export_endpoints(client: TestClient):
    """Verify report export HTTP endpoints."""
    sample_payload = {
        "filename": "pipeline.py",
        "quality_score": 88,
        "language": "python",
        "metrics": {"lines_of_code": 30, "function_count": 2},
        "findings": [],
        "recommendations": [],
    }

    # Direct HTML export
    res_html = client.post("/api/reports/export/html", json=sample_payload)
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "pipeline.py" in res_html.text

    # Direct JSON export
    res_json = client.post("/api/reports/export/json", json=sample_payload)
    assert res_json.status_code == 200
    assert res_json.json()["quality_score"] == 88


# ===================================================
# 5. History Storage & Local Persistence Tests
# ===================================================

def test_history_crud_operations(client: TestClient):
    """Verify saving, retrieving, listing, and deleting history scans."""
    # 1. Run single-file analysis which automatically saves to history
    res = client.post(
        "/api/analyze",
        json={"code": "def sample_func():\n    return 42\n", "language": "python", "filename": "sample.py"},
    )
    assert res.status_code == 200
    scan_id = res.json()["analysis_id"]

    # 2. List history
    list_res = client.post if False else client.get("/api/history")
    assert list_res.status_code == 200
    history_items = list_res.json()
    assert len(history_items) >= 1
    assert any(item["scan_id"] == scan_id for item in history_items)

    # 3. Get single scan
    detail_res = client.get(f"/api/history/{scan_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["analysis_id"] == scan_id

    # 4. Export report for this scan
    report_res = client.get(f"/api/reports/{scan_id}/html")
    assert report_res.status_code == 200
    assert "sample.py" in report_res.text

    # 5. Delete scan
    del_res = client.delete(f"/api/history/{scan_id}")
    assert del_res.status_code == 200

    # 6. Verify scan deleted
    get_after_del = client.get(f"/api/history/{scan_id}")
    assert get_after_del.status_code == 404
