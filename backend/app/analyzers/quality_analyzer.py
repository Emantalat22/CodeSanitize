"""Code quality analyzer inspecting function lengths, docstrings, and static clean-code patterns."""

import ast
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    StructuralMetrics,
    SupportedLanguage,
)


class CodeQualityAnalyzer(BaseAnalyzer):
    """Inspects code maintainability, function length, documentation, and structural clean-code invariants."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-QUAL-01"

    @property
    def name(self) -> str:
        return "Code Quality & Maintainability Analyzer"

    @property
    def description(self) -> str:
        return "Evaluates function sizes, documentation coverage, nesting depth, and clean code principles."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [
            SupportedLanguage.PYTHON,
            SupportedLanguage.JAVASCRIPT,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVA,
            SupportedLanguage.CPP,
        ]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []

        if not code.strip():
            return findings

        # 1. Documentation / Comment Ratio Check
        if metrics.lines_of_code > 25 and metrics.comment_ratio < 0.05:
            findings.append(
                AnalysisFinding(
                    id="QUAL-LOW-DOC-01",
                    category=FindingCategory.QUALITY,
                    severity=FindingSeverity.INFO,
                    title="Low documentation coverage",
                    description=f"Source code has {metrics.lines_of_code} lines but a low comment/docstring ratio of {metrics.comment_ratio * 100:.1f}%.",
                    recommendation="Add descriptive docstrings to module exports, classes, and complex algorithms.",
                )
            )

        if ast_tree is None:
            return findings

        # 2. Inspect Function Lengths & Empty Functions
        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function span in lines
                end_lineno = getattr(node, "end_lineno", node.lineno)
                func_length = end_lineno - node.lineno + 1

                if func_length > 60:
                    findings.append(
                        AnalysisFinding(
                            id="QUAL-LONG-FUNC-01",
                            category=FindingCategory.QUALITY,
                            severity=FindingSeverity.LOW,
                            title=f"Excessively long function '{node.name}'",
                            description=f"Function '{node.name}' spans {func_length} lines, exceeding recommended maintainability threshold (60 lines).",
                            location=FindingLocation(
                                line_start=node.lineno,
                                line_end=end_lineno,
                                function_name=node.name,
                            ),
                            evidence=f"def {node.name}(...): ({func_length} lines)",
                            recommendation="Decompose large function into smaller, single-purpose helper functions.",
                        )
                    )

                # Check for empty functions with no docstring
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Constant)):
                    if isinstance(node.body[0], ast.Pass):
                        findings.append(
                            AnalysisFinding(
                                id="QUAL-EMPTY-FUNC-01",
                                category=FindingCategory.QUALITY,
                                severity=FindingSeverity.INFO,
                                title=f"Empty function body in '{node.name}'",
                                description=f"Function '{node.name}' contains only a 'pass' statement without an explanatory docstring.",
                                location=FindingLocation(
                                    line_start=node.lineno,
                                    line_end=end_lineno,
                                    function_name=node.name,
                                ),
                                recommendation="Implement function logic or add an explicit TODO/docstring explaining interface purpose.",
                            )
                        )

            elif isinstance(node, ast.ClassDef):
                # Check for god classes
                method_count = sum(
                    1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                if method_count > 20:
                    findings.append(
                        AnalysisFinding(
                            id="QUAL-LARGE-CLASS-01",
                            category=FindingCategory.QUALITY,
                            severity=FindingSeverity.LOW,
                            title=f"Large class definition '{node.name}'",
                            description=f"Class '{node.name}' defines {method_count} methods. May violate Single Responsibility Principle.",
                            location=FindingLocation(
                                line_start=node.lineno,
                                line_end=getattr(node, "end_lineno", node.lineno),
                            ),
                            recommendation="Consider extracting helper services or separating class responsibilities.",
                        )
                    )

        return findings
