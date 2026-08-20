"""Cyclomatic and cognitive complexity analyzer for Python ASTs."""

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
from app.services.metrics_service import MetricsService


class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzes McCabe cyclomatic complexity, branch densities, loop counts, and nesting bottlenecks."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-CMPLX-01"

    @property
    def name(self) -> str:
        return "Cyclomatic Complexity & Control-Flow Analyzer"

    @property
    def description(self) -> str:
        return "Calculates McCabe cyclomatic complexity and identifies high-branching or deeply nested functions."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []

        if ast_tree is None:
            return findings

        complexity_metrics = MetricsService.calculate_complexity_metrics(ast_tree)

        # 1. Per-Function Cyclomatic Complexity Check
        for fn_metric in complexity_metrics.function_complexities:
            if fn_metric.cyclomatic_complexity > 15:
                findings.append(
                    AnalysisFinding(
                        id="CMPLX-HIGH-FUNC-01",
                        category=FindingCategory.COMPLEXITY,
                        severity=FindingSeverity.HIGH,
                        title=f"High complexity function '{fn_metric.name}'",
                        description=(
                            f"Function '{fn_metric.name}' has cyclomatic complexity of {fn_metric.cyclomatic_complexity} "
                            f"(threshold: 15) with {fn_metric.statement_count} statements."
                        ),
                        location=FindingLocation(
                            line_start=fn_metric.line_start,
                            function_name=fn_metric.name,
                        ),
                        evidence=f"Cyclomatic complexity: {fn_metric.cyclomatic_complexity}",
                        recommendation="Refactor function into smaller sub-routines and simplify conditional branching.",
                    )
                )
            elif fn_metric.cyclomatic_complexity > 8:
                findings.append(
                    AnalysisFinding(
                        id="CMPLX-MED-FUNC-01",
                        category=FindingCategory.COMPLEXITY,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Moderate complexity function '{fn_metric.name}'",
                        description=(
                            f"Function '{fn_metric.name}' has cyclomatic complexity of {fn_metric.cyclomatic_complexity} "
                            f"(threshold: 8)."
                        ),
                        location=FindingLocation(
                            line_start=fn_metric.line_start,
                            function_name=fn_metric.name,
                        ),
                        evidence=f"Cyclomatic complexity: {fn_metric.cyclomatic_complexity}",
                        recommendation="Consider extracting helper functions to reduce decision branches.",
                    )
                )

            # 2. Per-Function Deep Nesting Check
            if fn_metric.nesting_depth > 4:
                findings.append(
                    AnalysisFinding(
                        id="CMPLX-DEEP-NEST-01",
                        category=FindingCategory.COMPLEXITY,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Excessive nesting depth in '{fn_metric.name}'",
                        description=(
                            f"Function '{fn_metric.name}' reaches a nesting depth of {fn_metric.nesting_depth} "
                            f"(recommended max: 4)."
                        ),
                        location=FindingLocation(
                            line_start=fn_metric.line_start,
                            function_name=fn_metric.name,
                        ),
                        evidence=f"Max nesting: {fn_metric.nesting_depth}",
                        recommendation="Use early return guards (guard clauses) to flatten nested blocks.",
                    )
                )

        # 3. Overall Module Complexity Check
        if complexity_metrics.cyclomatic_complexity > 40:
            findings.append(
                AnalysisFinding(
                    id="CMPLX-HIGH-MODULE-01",
                    category=FindingCategory.COMPLEXITY,
                    severity=FindingSeverity.LOW,
                    title="High overall module complexity",
                    description=(
                        f"Module cumulative cyclomatic complexity is {complexity_metrics.cyclomatic_complexity} "
                        f"across {complexity_metrics.branching_count} branches and {complexity_metrics.loop_count} loops."
                    ),
                    recommendation="Consider splitting module into focused sub-packages or service classes.",
                )
            )

        return findings
