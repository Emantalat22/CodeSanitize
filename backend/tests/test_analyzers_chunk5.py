"""Comprehensive tests for Chunk 5 Advanced Code Analysis and Intelligence Layer."""

import ast
import pytest
from fastapi.testclient import TestClient
from app.analyzers.complexity_analyzer import ComplexityAnalyzer
from app.analyzers.fingerprint_analyzer import FingerprintAnalyzer
from app.analyzers.quality_analyzer import CodeQualityAnalyzer
from app.analyzers.registry import AnalyzerRegistry
from app.analyzers.security_analyzer import SecurityPatternAnalyzer
from app.analyzers.similarity_engine import SimilarityAnalyzer
from app.models.schemas import (
    FindingCategory,
    FindingSeverity,
    StructuralMetrics,
    SupportedLanguage,
)
from app.services.metrics_service import MetricsService


@pytest.fixture
def empty_metrics():
    return StructuralMetrics(lines_of_code=0, raw_character_count=0)


# ===================================================
# 1. Code Quality Analyzer Tests
# ===================================================

def test_quality_analyzer_empty_code(empty_metrics):
    """Verify quality analyzer handles empty code gracefully."""
    analyzer = CodeQualityAnalyzer()
    findings = analyzer.analyze("", None, empty_metrics, {})
    assert len(findings) == 0


def test_quality_analyzer_detects_empty_function_and_low_doc():
    """Verify quality analyzer detects empty functions without docstrings."""
    code = "def stub():\n    pass\n"
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = CodeQualityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    empty_findings = [f for f in findings if f.id == "QUAL-EMPTY-FUNC-01"]
    assert len(empty_findings) == 1
    assert "stub" in empty_findings[0].title


def test_quality_analyzer_long_function():
    """Verify quality analyzer flags functions exceeding maintainability limits."""
    lines = ["def huge_function():"] + [f"    x_{i} = {i}" for i in range(70)] + ["    return x_0"]
    code = "\n".join(lines)
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = CodeQualityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    long_func_findings = [f for f in findings if f.id == "QUAL-LONG-FUNC-01"]
    assert len(long_func_findings) == 1
    assert "huge_function" in long_func_findings[0].title


# ===================================================
# 2. Complexity Analyzer Tests
# ===================================================

def test_complexity_analyzer_branching_and_loops():
    """Verify cyclomatic complexity increases with branching and loops."""
    code = """def complex_logic(a, b, c):
    if a > 0:
        for i in range(10):
            if b:
                while c > 0:
                    try:
                        c -= 1
                    except ValueError:
                        break
    return a + b + c
"""
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = ComplexityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    c_metrics = MetricsService.calculate_complexity_metrics(tree)
    assert c_metrics.cyclomatic_complexity > 5
    assert c_metrics.loop_count >= 2
    assert c_metrics.branching_count >= 2
    assert c_metrics.exception_handling_count == 1
    assert c_metrics.max_nesting_depth >= 4


def test_complexity_analyzer_flags_high_complexity_function():
    """Verify complexity analyzer reports high complexity functions with refactoring recommendations."""
    lines = ["def branching_monster(x):", "    res = 0"]
    for i in range(16):
        lines.append(f"    if x == {i}: res += {i}")
    lines.append("    return res")
    code = "\n".join(lines)

    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = ComplexityAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    high_c = [f for f in findings if f.id == "CMPLX-HIGH-FUNC-01"]
    assert len(high_c) == 1
    assert high_c[0].severity == FindingSeverity.HIGH
    assert "branching_monster" in high_c[0].title
    assert "Refactor" in high_c[0].recommendation


# ===================================================
# 3. Static Security Pattern Analyzer Tests
# ===================================================

def test_security_analyzer_detects_eval_and_exec():
    """Verify static security analyzer detects eval and exec calls without executing them."""
    code = """def run_user_input(code_str, expr_str):
    eval(expr_str)
    exec(code_str)
"""
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = SecurityPatternAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    eval_findings = [f for f in findings if f.id == "SEC-EVAL-01"]
    exec_findings = [f for f in findings if f.id == "SEC-EXEC-01"]
    assert len(eval_findings) == 1
    assert eval_findings[0].severity == FindingSeverity.CRITICAL
    assert len(exec_findings) == 1
    assert exec_findings[0].severity == FindingSeverity.CRITICAL


def test_security_analyzer_detects_subprocess_shell_true():
    """Verify detection of subprocess with shell=True."""
    code = """import subprocess

def run_cmd(cmd):
    subprocess.run(cmd, shell=True)
"""
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = SecurityPatternAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    shell_findings = [f for f in findings if f.id == "SEC-SUBPROCESS-SHELL-01"]
    assert len(shell_findings) == 1
    assert shell_findings[0].severity == FindingSeverity.HIGH


def test_security_analyzer_detects_weak_crypto_and_sql_concat():
    """Verify detection of hashlib.md5 and SQL string concatenation."""
    code = """import hashlib
import sqlite3

def query_and_hash(user_id, raw_pass):
    h = hashlib.md5(raw_pass.encode()).hexdigest()
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
"""
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = SecurityPatternAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    crypto_findings = [f for f in findings if f.id == "SEC-WEAK-CRYPTO-01"]
    sql_findings = [f for f in findings if f.id == "SEC-SQL-CONCAT-01"]
    assert len(crypto_findings) == 1
    assert len(sql_findings) == 1


def test_security_analyzer_detects_hardcoded_secrets():
    """Verify static pattern detection of hardcoded API tokens and secret keys."""
    code = """# Configuration
API_KEY = "sk_live_983749283749283749283"
DATABASE_URL = "postgres://localhost"
"""
    tree = ast.parse(code)
    metrics = MetricsService.calculate_structural_metrics(code, tree)
    analyzer = SecurityPatternAnalyzer()
    findings = analyzer.analyze(code, tree, metrics, {})

    secret_findings = [f for f in findings if f.id == "SEC-SECRET-HARDCODED-01"]
    assert len(secret_findings) == 1
    assert secret_findings[0].severity == FindingSeverity.HIGH


# ===================================================
# 4. Fingerprint & Similarity Engine Tests
# ===================================================

def test_fingerprint_identical_for_identifier_renamed_code():
    """Verify that def add(a,b): return a+b and def sum_values(x,y): return x+y have identical structural fingerprints."""
    code_a = "def add(a, b):\n    return a + b\n"
    code_b = "def sum_values(x, y):\n    return x + y\n"

    tree_a = ast.parse(code_a)
    tree_b = ast.parse(code_b)

    fp_a = FingerprintAnalyzer.generate_fingerprint(tree_a)
    fp_b = FingerprintAnalyzer.generate_fingerprint(tree_b)

    assert fp_a.ast_node_hash == fp_b.ast_node_hash
    assert fp_a.structure_vector == fp_b.structure_vector

    sim = SimilarityAnalyzer.calculate_similarity(fp_a, fp_b)
    assert sim.score == 100.0
    assert "Identical" in sim.explanation


def test_fingerprint_different_for_different_structures():
    """Verify different structural code snippets have different fingerprints."""
    code_a = "def add(a, b): return a + b\n"
    code_b = "class Model:\n    def __init__(self):\n        for i in range(5): print(i)\n"

    tree_a = ast.parse(code_a)
    tree_b = ast.parse(code_b)

    fp_a = FingerprintAnalyzer.generate_fingerprint(tree_a)
    fp_b = FingerprintAnalyzer.generate_fingerprint(tree_b)

    assert fp_a.ast_node_hash != fp_b.ast_node_hash
    sim = SimilarityAnalyzer.calculate_similarity(fp_a, fp_b)
    assert sim.score < 100.0


# ===================================================
# 5. POST /api/analyze Integration Tests
# ===================================================

def test_api_analyze_returns_comprehensive_intelligence(client: TestClient):
    """Verify POST /api/analyze returns overall score, complexity metrics, findings, and analyzer reports."""
    code = """import os
import subprocess

def process_data(items: list[int]) -> int:
    \"\"\"Sum even numbers.\"\"\"
    total = 0
    for item in items:
        if item % 2 == 0:
            total += item
    return total
"""
    res = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "filename": "sample.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["analysis_status"] == "completed"
    assert data["overall_score"] > 0
    assert "complexity_metrics" in data
    assert data["complexity_metrics"]["cyclomatic_complexity"] >= 3
    assert len(data["analyzer_reports"]) >= 4
    assert data["fingerprint"] is not None
    assert "ast_node_hash" in data["fingerprint"]


def test_api_analyze_syntax_error_handling(client: TestClient):
    """Verify POST /api/analyze handles syntax errors gracefully without crashing."""
    invalid_code = "def broken(:\n    pass\n"
    res = client.post(
        "/api/analyze",
        json={"code": invalid_code, "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["syntax_valid"] is False
    assert data["analysis_status"] == "syntax_error"
    assert len(data["issues"]) > 0
    assert data["overall_score"] == 0


def test_api_analyze_empty_code(client: TestClient):
    """Verify POST /api/analyze handles empty code safely."""
    res = client.post(
        "/api/analyze",
        json={"code": "", "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["syntax_valid"] is True
    assert data["analysis_status"] == "completed"
    assert data["line_count"] == 0
