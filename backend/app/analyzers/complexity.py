"""Complexity Analyzer for McCabe Cyclomatic Complexity, Nesting, and Function Ranking."""

import ast
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    CodeMetrics,
    ComplexityFunction,
    ComplexityFunctionMetric,
    ComplexityReport,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    SupportedLanguage,
)


class FunctionComplexityVisitor(ast.NodeVisitor):
    """AST visitor to compute cyclomatic complexity, nesting, and statement count for a function."""

    def __init__(self, function_name: str, line_start: int):
        self.function_name = function_name
        self.line_start = line_start
        self.complexity = 1
        self.current_nesting = 0
        self.max_nesting = 1
        self.statement_count = 0

    def generic_visit(self, node: ast.AST):
        if isinstance(node, ast.stmt):
            self.statement_count += 1
        super().generic_visit(node)

    def _enter_nested_block(self, node: ast.AST):
        self.current_nesting += 1
        if self.current_nesting > self.max_nesting:
            self.max_nesting = self.current_nesting
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self._enter_nested_block(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self._enter_nested_block(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.complexity += 1
        self._enter_nested_block(node)

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self._enter_nested_block(node)

    def visit_Try(self, node: ast.Try):
        self.complexity += len(node.handlers)
        self._enter_nested_block(node)

    def visit_With(self, node: ast.With):
        self._enter_nested_block(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._enter_nested_block(node)

    def visit_Match(self, node: Any):
        if hasattr(node, "cases"):
            self.complexity += max(len(node.cases) - 1, 1)
        self._enter_nested_block(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        # Each 'and' / 'or' condition adds a decision branch point
        self.complexity += max(len(node.values) - 1, 1)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.generic_visit(node)


class ComplexityAnalyzer(BaseAnalyzer):
    """Calculates McCabe cyclomatic complexity, control flow branches, and nesting rankings."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-CMPLX-01"

    @property
    def name(self) -> str:
        return "Cyclomatic Complexity & Control-Flow Analyzer"

    @property
    def description(self) -> str:
        return "Measures McCabe cyclomatic complexity, control-flow branching, loop counts, and block nesting depths."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: CodeMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        """Inspect complexity and flag maintainability hotspots."""
        findings: List[AnalysisFinding] = []
        if ast_tree is None:
            return findings

        report = self.compute_complexity(ast_tree)

        # 1. Flag high cyclomatic complexity functions
        for fn in report.most_complex_functions:
            if fn.complexity > 15:
                findings.append(
                    AnalysisFinding(
                        id="CMPLX-HIGH-MCCABE-01",
                        category=FindingCategory.COMPLEXITY,
                        severity=FindingSeverity.HIGH,
                        title=f"High cyclomatic complexity in '{fn.name}'",
                        description=f"Function '{fn.name}' has cyclomatic complexity of {fn.complexity} (recommended: <= 10).",
                        location=FindingLocation(
                            line_start=fn.line_start,
                            function_name=fn.name,
                        ),
                        recommendation="Refactor and decompose complex conditionals into smaller sub-methods.",
                    )
                )
            elif fn.complexity > 8:
                findings.append(
                    AnalysisFinding(
                        id="CMPLX-MODERATE-MCCABE-01",
                        category=FindingCategory.COMPLEXITY,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Moderate cyclomatic complexity in '{fn.name}'",
                        description=f"Function '{fn.name}' has cyclomatic complexity of {fn.complexity} (threshold: 8).",
                        location=FindingLocation(
                            line_start=fn.line_start,
                            function_name=fn.name,
                        ),
                        recommendation="Consider extracting helper functions or simplifying boolean logic.",
                    )
                )

        # 2. Flag deep nesting blocks
        if report.max_nesting_depth > 4:
            findings.append(
                AnalysisFinding(
                    id="CMPLX-DEEP-NEST-01",
                    category=FindingCategory.COMPLEXITY,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Excessive nesting depth ({report.max_nesting_depth} levels)",
                    description=f"Maximum block nesting depth is {report.max_nesting_depth} (recommended: <= 3).",
                    recommendation="Use early return guards (guard clauses) to flatten nested blocks.",
                )
            )

        return findings

    @classmethod
    def compute_complexity(cls, ast_tree: Optional[ast.AST]) -> ComplexityReport:
        """Calculate complete ComplexityReport including function rankings."""
        if ast_tree is None:
            return ComplexityReport()

        branching_count = 0
        loop_count = 0
        exception_count = 0
        total_module_complexity = 1
        max_nesting = 0

        function_complexities: List[ComplexityFunctionMetric] = []
        ranked_functions: List[ComplexityFunction] = []

        # Count global branching statements
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.If):
                branching_count += 1
                total_module_complexity += 1
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                loop_count += 1
                total_module_complexity += 1
            elif isinstance(node, ast.Try):
                exception_count += len(node.handlers)
                total_module_complexity += len(node.handlers)
            elif isinstance(node, ast.BoolOp):
                total_module_complexity += max(len(node.values) - 1, 1)
            elif isinstance(node, ast.IfExp):
                total_module_complexity += 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                total_module_complexity += len(node.generators)


        # Analyze individual functions and methods
        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = FunctionComplexityVisitor(
                    function_name=node.name,
                    line_start=node.lineno,
                )
                for stmt in node.body:
                    visitor.visit(stmt)

                if visitor.max_nesting > max_nesting:
                    max_nesting = visitor.max_nesting

                # Determine risk level
                if visitor.complexity > 15:
                    risk = "high"
                elif visitor.complexity > 8:
                    risk = "medium"
                else:
                    risk = "low"

                function_complexities.append(
                    ComplexityFunctionMetric(
                        name=node.name,
                        line_start=node.lineno,
                        cyclomatic_complexity=visitor.complexity,
                        nesting_depth=visitor.max_nesting,
                        statement_count=visitor.statement_count,
                    )
                )

                ranked_functions.append(
                    ComplexityFunction(
                        name=node.name,
                        complexity=visitor.complexity,
                        risk=risk,
                        line_start=node.lineno,
                        nesting_depth=visitor.max_nesting,
                        statement_count=visitor.statement_count,
                    )
                )

        # Sort functions by complexity descending
        ranked_functions.sort(key=lambda f: f.complexity, reverse=True)

        # Compute summary metrics
        if ranked_functions:
            avg_comp = round(sum(f.complexity for f in ranked_functions) / len(ranked_functions), 1)
            max_comp = ranked_functions[0].complexity
        else:
            avg_comp = float(total_module_complexity)
            max_comp = total_module_complexity

        if max_comp > 15 or total_module_complexity > 20:
            level = "High"
        elif max_comp > 8 or total_module_complexity > 10:
            level = "Medium"
        else:
            level = "Low"

        return ComplexityReport(
            average_complexity=avg_comp,
            maximum_complexity=max_comp,
            most_complex_functions=ranked_functions,
            complexity_level=level,
            cyclomatic_complexity=total_module_complexity,
            branching_count=branching_count,
            loop_count=loop_count,
            max_nesting_depth=max_nesting,
            exception_handling_count=exception_count,
            function_complexities=function_complexities,
        )
