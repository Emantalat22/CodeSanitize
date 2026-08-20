"""Comprehensive unit and integration tests for CodeSanitize Analysis Engine."""

import pytest
from fastapi.testclient import TestClient
from app.models.schemas import (
    AnalysisStatus,
    CodeInput,
    IssueSeverity,
    SupportedLanguage,
)
from app.services.analysis_service import AnalysisService


# ==========================================
# 1. Python Parser Tests
# ==========================================

def test_python_valid_code_analysis(client: TestClient):
    """Test valid Python function parsing, syntax validity, and metrics."""
    code = """def add(a: int, b: int) -> int:
    # Perform arithmetic addition
    return a + b
"""
    response = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "filename": "math_utils.py"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["syntax_valid"] is True
    assert data["analysis_status"] == "completed"
    assert data["language"] == "python"
    assert data["filename"] == "math_utils.py"
    assert data["parser_used"] == "Python Built-in AST & Tokenizer"

    metrics = data["structural_metrics"]
    assert metrics["function_count"] == 1
    assert metrics["class_count"] == 0
    assert metrics["import_count"] == 0
    assert metrics["ast_nodes_count"] > 0
    assert metrics["comment_count"] >= 1
    assert data["capabilities"]["ast_available"] is True


def test_python_invalid_syntax(client: TestClient):
    """Test Python code with missing colon reports syntax error with line/column info."""
    code = """def add(a, b)
    return a + b
"""
    response = client.post(
        "/api/analyze",
        json={"code": code, "language": "python"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["syntax_valid"] is False
    assert data["analysis_status"] == "syntax_error"
    assert len(data["issues"]) > 0

    first_issue = data["issues"][0]
    assert first_issue["severity"] == "error"
    assert first_issue["line_start"] == 1
    assert first_issue["column_start"] is not None
    assert "syntax" in first_issue["message"].lower() or "invalid" in first_issue["message"].lower() or "expected" in first_issue["message"].lower()


def test_python_class_counting():
    """Verify class counting in Python AST."""
    code = """class BaseService:
    \"\"\"Base service docstring.\"\"\"
    pass

class AuthProcessor(BaseService):
    def process(self):
        pass

class TokenValidator:
    pass
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.class_count == 3
    assert result.structural_metrics.function_count == 1
    assert result.structural_metrics.docstring_count >= 1


def test_python_import_counting():
    """Verify import statement counting."""
    code = """import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Optional
import math as m
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.import_count == 5


def test_python_control_flow_and_nesting():
    """Verify control flow nodes, nesting depth, and cyclomatic complexity."""
    code = """def complex_logic(x: int, items: list[int]) -> int:
    total = 0
    if x > 0:
        for item in items:
            if item % 2 == 0:
                while item > 0:
                    total += item
                    item -= 1
            else:
                total -= 1
    elif x == 0:
        total = 0
    else:
        total = -1
    return total
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )
    assert result.syntax_valid is True
    metrics = result.structural_metrics
    assert metrics.function_count == 1
    assert metrics.control_flow_node_count >= 4
    assert metrics.max_nesting_depth >= 4
    assert metrics.cyclomatic_complexity >= 5


def test_empty_source_handling(client: TestClient):
    """Verify empty source is handled gracefully without crashing."""
    response = client.post(
        "/api/analyze",
        json={"code": "", "language": "python"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["syntax_valid"] is True
    assert data["code_length"] == 0
    assert data["line_count"] == 0


def test_unicode_source_handling():
    """Verify Unicode code with emojis, non-ASCII identifiers, and strings does not crash."""
    code = """# 🚀 Rocket calculation
def 计算_总和(数值_一: int, 数值_二: int) -> str:
    \"\"\"返回带表情的结果 ✨\"\"\"
    greeting = "Hello, 世界! 🌍"
    return f"{greeting}: {数值_一 + 数值_二}"
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.function_count == 1
    assert result.structural_metrics.docstring_count >= 1


# ==========================================
# 2. Multi-Language (Tree-sitter) Tests
# ==========================================

def test_javascript_parser_analysis(client: TestClient):
    """Test JavaScript code parsing via Tree-sitter."""
    code = """import { useState } from 'react';

export class DataStore {
    constructor() {
        this.items = [];
    }
}

function processData(input) {
    if (!input) {
        return null;
    }
    const result = input.map(x => x * 2);
    return result;
}
"""
    response = client.post(
        "/api/analyze",
        json={"code": code, "language": "javascript", "filename": "store.js"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["syntax_valid"] is True
    assert data["analysis_status"] == "completed"
    assert "Tree-sitter" in data["parser_used"]

    metrics = data["structural_metrics"]
    assert metrics["import_count"] >= 1
    assert metrics["class_count"] >= 1
    assert metrics["function_count"] >= 2  # constructor/processData/arrow
    assert metrics["ast_nodes_count"] > 10


def test_typescript_parser_analysis():
    """Test TypeScript code parsing with type annotations."""
    code = """interface User {
    id: string;
    name: string;
}

export class UserService {
    private users: User[] = [];

    public findUser(id: string): User | undefined {
        return this.users.find(u => u.id === id);
    }
}
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.TYPESCRIPT)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.class_count >= 1  # class / interface
    assert result.structural_metrics.function_count >= 1


def test_java_parser_analysis():
    """Test Java class and method parsing."""
    code = """package com.example.demo;

import java.util.List;
import java.util.ArrayList;

public class Calculator {
    private List<Integer> history = new ArrayList<>();

    public int add(int a, int b) {
        int sum = a + b;
        history.add(sum);
        return sum;
    }
}
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.JAVA)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.import_count == 2
    assert result.structural_metrics.class_count == 1
    assert result.structural_metrics.function_count >= 1


def test_cpp_parser_analysis():
    """Test C++ code parsing."""
    code = """#include <iostream>
#include <vector>

class Engine {
public:
    void start() {
        std::cout << "Engine started" << std::endl;
    }
};

int main() {
    Engine e;
    e.start();
    return 0;
}
"""
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.CPP)
    )
    assert result.syntax_valid is True
    assert result.structural_metrics.import_count == 2  # preproc_include
    assert result.structural_metrics.class_count == 1
    assert result.structural_metrics.function_count >= 2


def test_javascript_syntax_error():
    """Test JavaScript syntax error detection."""
    code = "function broken( { return 1; }"
    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.JAVASCRIPT)
    )
    assert result.syntax_valid is False
    assert result.analysis_status == AnalysisStatus.SYNTAX_ERROR
    assert len(result.issues) > 0


# ==========================================
# 3. Non-functional Artifacts Detection
# ==========================================

def test_nonfunctional_artifacts_detection():
    """Test detection of trailing whitespace, mixed indentation, excessive blank lines, and zero-width characters."""
    code = "# -*- coding: utf-8 -*-\n"
    code += "def sample():   \n"  # Trailing whitespace
    code += "    a = 1\n"
    code += "\t\t b = 2\n"  # Mixed indent
    code += "\n\n\n\n"  # Excessive blank lines (4 empty lines)
    code += "# Hidden\u200Bzero width space\n"  # U+200B zero-width space
    code += "    return a + b\n"

    result = AnalysisService.analyze(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )
    artifacts = result.detected_nonfunctional_artifacts
    kinds = [art.kind for art in artifacts]

    assert "trailing_whitespace" in kinds
    assert "mixed_indentation" in kinds or "inconsistent_indentation_style" in kinds
    assert "excessive_blank_lines" in kinds
    assert "unusual_unicode_character" in kinds
    assert "source_encoding_declaration" in kinds


# ==========================================
# 4. Security & Safety Limits
# ==========================================

def test_max_source_size_guard():
    """Verify payload exceeding 2MB is rejected by security guard."""
    oversized_code = "x = 1\n" * 400_000  # ~2.4 MB
    result = AnalysisService.analyze(
        CodeInput(code=oversized_code, language=SupportedLanguage.PYTHON)
    )
    assert result.syntax_valid is False
    assert result.analysis_status == AnalysisStatus.FAILED
    assert any("size" in issue.message.lower() for issue in result.issues)


def test_filename_traversal_sanitization():
    """Verify path traversal filenames are safely stripped."""
    result = AnalysisService.analyze(
        CodeInput(
            code="pass",
            language=SupportedLanguage.PYTHON,
            filename="../../etc/passwd",
        )
    )
    assert result.filename == "passwd"
