"""Comprehensive unit and integration tests for Chunk 5 Real Static Code Intelligence Engine."""

import ast
import pytest
from fastapi.testclient import TestClient
from app.analyzers.code_metrics import CodeMetricsAnalyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.registry import AnalyzerRegistry
from app.analyzers.security import SecurityAnalyzer
from app.main import app
from app.models.schemas import (
    CodeMetrics,
    FindingCategory,
    FindingSeverity,
    SupportedLanguage,
)
from app.services.quality_service import QualityService



# ===================================================
# 1. Code Metrics Analyzer Tests
# ===================================================


def test_code_metrics_empty_file():
    """Verify code metrics analyzer correctly processes empty files."""
    code = ""
    tree = None
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)

    assert metrics.lines_of_code == 0
    assert metrics.function_count == 0
    assert metrics.class_count == 0
    assert metrics.import_count == 0
    assert metrics.blank_lines == 0
    assert metrics.comment_lines == 0

    analyzer = CodeMetricsAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})
    assert len(findings) == 1
    assert findings[0].id == "METRICS-EMPTY-FILE"


def test_code_metrics_simple_function():
    """Verify code metrics analyzer calculates LOC, docstrings, and comments for simple functions."""
    code = '''# Mathematical utility module
def square(x: int) -> int:
    """Return x squared."""
    return x * x
'''
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)

    assert metrics.lines_of_code == 4
    assert metrics.function_count == 1
    assert metrics.class_count == 0
    assert metrics.docstring_count == 1
    assert metrics.comment_lines == 1
    assert metrics.comment_ratio > 0.0



def test_code_metrics_class_based_code():
    """Verify code metrics analyzer accurately counts classes, methods, and imports."""
    code = '''import os
from typing import List

class UserAccount:
    """User account model."""
    
    def __init__(self, username: str):
        self.username = username
        
    def get_display_name(self) -> str:
        return self.username.strip()
'''
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)

    assert metrics.class_count == 1
    assert metrics.function_count == 2
    assert metrics.import_count == 2
    assert metrics.docstring_count == 1
    assert metrics.lines_of_code > 10


# ===================================================
# 2. Complexity Analyzer Tests
# ===================================================

def test_complexity_analyzer_nested_conditions_and_nesting():
    """Verify calculation of nesting depth and nested if conditions."""
    code = '''def check_access(user, role, perm):
    if user.is_authenticated:
        if role.is_admin:
            if perm == "WRITE":
                return True
    return False
'''
    tree = ast.parse(code)
    report = ComplexityAnalyzer.compute_complexity(tree)

    assert report.max_nesting_depth >= 3
    assert report.branching_count == 3
    assert len(report.most_complex_functions) == 1
    assert report.most_complex_functions[0].name == "check_access"
    assert report.most_complex_functions[0].complexity >= 4


def test_complexity_analyzer_loops_and_comprehensions():
    """Verify loop statements and list comprehensions increment cyclomatic score."""
    code = '''def process_numbers(matrix):
    total = 0
    for row in matrix:
        while len(row) > 0:
            val = row.pop()
            total += val
    evens = [x for x in range(10) if x % 2 == 0]
    return total + sum(evens)
'''
    tree = ast.parse(code)
    report = ComplexityAnalyzer.compute_complexity(tree)

    assert report.loop_count >= 2
    assert report.cyclomatic_complexity >= 4
    assert len(report.most_complex_functions) == 1


def test_complexity_analyzer_exception_handling():
    """Verify try/except handler branches are tracked in complexity report."""
    code = '''def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0
    except TypeError:
        return -1
'''
    tree = ast.parse(code)
    report = ComplexityAnalyzer.compute_complexity(tree)

    assert report.exception_handling_count == 2
    assert report.cyclomatic_complexity >= 3


# ===================================================
# 3. Security Analyzer Tests
# ===================================================

def test_security_analyzer_detects_eval():
    """Verify static detection of eval() calls as Critical severity."""
    code = 'user_input = "2 + 2"\nresult = eval(user_input)\n'
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    analyzer = SecurityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    eval_findings = [f for f in findings if f.id == "SEC-EVAL-01"]
    assert len(eval_findings) == 1
    assert eval_findings[0].severity == FindingSeverity.CRITICAL


def test_security_analyzer_detects_exec():
    """Verify static detection of exec() calls as Critical severity."""
    code = 'payload = "print(1)"\nexec(payload)\n'
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    analyzer = SecurityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    exec_findings = [f for f in findings if f.id == "SEC-EXEC-01"]
    assert len(exec_findings) == 1
    assert exec_findings[0].severity == FindingSeverity.CRITICAL


def test_security_analyzer_detects_subprocess_shell_true():
    """Verify static detection of subprocess calls with shell=True as High severity."""
    code = 'import subprocess\nsubprocess.run("ls -la " + target, shell=True)\n'
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    analyzer = SecurityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    subproc_findings = [f for f in findings if f.id == "SEC-SUBPROCESS-SHELL-01"]
    assert len(subproc_findings) == 1
    assert subproc_findings[0].severity == FindingSeverity.HIGH


def test_security_analyzer_report_generation():
    """Verify SecurityReport aggregation accurately categorizes risk levels."""
    code = '''import hashlib
# Secret credentials
API_KEY = "sk_live_1234567890abcdef1234"

def hash_pass(p):
    return hashlib.md5(p.encode()).hexdigest()
'''
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    analyzer = SecurityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})
    report = SecurityAnalyzer.generate_report(findings)

    assert report.warning_count >= 1
    assert report.risk_level in ("High", "Medium")
    assert len(report.findings) >= 2


# ===================================================
# 4. Quality Service Scoring Tests
# ===================================================

def test_quality_service_clean_code_scoring():
    """Verify clean code receives realistic optimal scores (e.g. 90-95, not unrealistic 100)."""
    code = '''"""Math utilities."""

def calculate_average(values: list[float]) -> float:
    """Calculate mean of numbers."""
    if not values:
        return 0.0
    return sum(values) / len(values)
'''
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    complexity = ComplexityAnalyzer.compute_complexity(tree)
    score = QualityService.calculate_quality_score([], complexity, metrics)

    assert 85 <= score <= 98


def test_quality_service_vulnerable_code_penalties():
    """Verify security vulnerabilities and deep nesting heavily penalize the quality score."""
    code = 'eval("1 + 1")\n'
    tree = ast.parse(code)
    metrics = CodeMetricsAnalyzer.compute_metrics(code, tree)
    complexity = ComplexityAnalyzer.compute_complexity(tree)
    analyzer = SecurityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})
    score = QualityService.calculate_quality_score(findings, complexity, metrics)

    assert score <= 70


# ===================================================
# 5. POST /api/analyze Integration Tests
# ===================================================

def test_api_analyze_valid_python_code(client: TestClient):
    """Verify POST /api/analyze returns comprehensive structured AnalysisResult with real metrics."""
    code = '''"""Data processing pipeline."""
import json

def process_records(raw_data: str) -> dict:
    """Parse JSON and count valid items."""
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return {"count": 0, "status": "error"}
        
    return {"count": len(data), "status": "ok"}
'''
    res = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "filename": "processor.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["analysis_status"] == "completed"
    assert data["quality_score"] > 80
    assert data["metrics"]["lines_of_code"] > 0
    assert data["metrics"]["function_count"] == 1
    assert data["metrics"]["import_count"] == 1
    assert "complexity_report" in data
    assert data["complexity_report"]["average_complexity"] >= 1.0
    assert "security_report" in data
    assert data["security_report"]["risk_level"] in ("Clean", "Low")
    assert isinstance(data["findings"], list)
    assert isinstance(data["recommendations"], list)


def test_api_analyze_invalid_syntax(client: TestClient):
    """Verify POST /api/analyze returns syntax_valid=False and quality_score=0 on broken syntax."""
    code = "def broken_func(:\n    return\n"
    res = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "filename": "broken.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is False
    assert data["analysis_status"] == "syntax_error"
    assert data["quality_score"] == 0
    assert len(data["issues"]) > 0


def test_api_analyze_empty_input(client: TestClient):
    """Verify POST /api/analyze gracefully handles empty input without crashing."""
    res = client.post(
        "/api/analyze",
        json={"code": "", "language": "python", "filename": "empty.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["quality_score"] == 0
    assert data["metrics"]["lines_of_code"] == 0
