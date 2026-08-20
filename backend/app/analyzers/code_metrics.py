"""Code Metrics Analyzer for physical and AST structural metrics."""

import ast
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    CodeMetrics,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    SupportedLanguage,
)


class CodeMetricsAnalyzer(BaseAnalyzer):
    """Calculates comprehensive physical lines, comments, functions, classes, and AST metrics."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-METRICS-01"

    @property
    def name(self) -> str:
        return "Code Metrics & Structural Analyzer"

    @property
    def description(self) -> str:
        return "Analyzes physical lines, blank lines, comments, AST functions, classes, and import declarations."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [
            SupportedLanguage.PYTHON,
            SupportedLanguage.JAVASCRIPT,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVA,
            SupportedLanguage.CPP,
            SupportedLanguage.C,
        ]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: CodeMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        """Perform metrics inspection and report structural findings."""
        findings: List[AnalysisFinding] = []

        # 1. Flag empty file
        if not code.strip():
            findings.append(
                AnalysisFinding(
                    id="METRICS-EMPTY-FILE",
                    category=FindingCategory.QUALITY,
                    severity=FindingSeverity.INFO,
                    title="Empty source file",
                    description="The submitted source file contains 0 executable statements.",
                    recommendation="Provide source code statements to perform static analysis.",
                )
            )
            return findings

        # 2. Check for low documentation ratio
        if metrics.lines_of_code > 10 and metrics.comment_ratio < 0.05:
            findings.append(
                AnalysisFinding(
                    id="METRICS-LOW-DOC",
                    category=FindingCategory.QUALITY,
                    severity=FindingSeverity.LOW,
                    title="Low documentation density",
                    description=f"Documentation ratio is {round(metrics.comment_ratio * 100, 1)}% across {metrics.lines_of_code} LOC.",
                    recommendation="Add function docstrings and explanatory module comments.",
                )
            )

        # 3. Check for oversized functions
        if ast_tree is not None:
            for node in ast.walk(ast_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_loc = (node.end_lineno or node.lineno) - node.lineno + 1
                    if func_loc > 50:
                        findings.append(
                            AnalysisFinding(
                                id="METRICS-LONG-FUNCTION",
                                category=FindingCategory.QUALITY,
                                severity=FindingSeverity.MEDIUM,
                                title=f"Large function body: '{node.name}'",
                                description=f"Function '{node.name}' spans {func_loc} lines (recommended: <= 30 lines).",
                                location=FindingLocation(
                                    line_start=node.lineno,
                                    line_end=node.end_lineno,
                                    function_name=node.name,
                                ),
                                recommendation="Decompose large function into smaller modular helper routines.",
                            )
                        )

        return findings

    @classmethod
    def compute_metrics(cls, code: str, ast_tree: Optional[ast.AST]) -> CodeMetrics:
        """Compute exact CodeMetrics from raw source code and AST."""
        lines = code.splitlines() if code else []
        loc = len(lines)
        raw_chars = len(code)

        blank_lines = 0
        comment_lines = 0
        docstring_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif (
                stripped.startswith("#")
                or stripped.startswith("//")
                or stripped.startswith("/*")
                or stripped.startswith("*")
            ):
                comment_lines += 1

        function_count = 0
        class_count = 0
        import_count = 0
        assignment_count = 0
        control_flow_count = 0
        ast_nodes_count = 0
        max_nesting = 0
        cyclomatic = 1

        if ast_tree is not None:
            for node in ast.walk(ast_tree):
                ast_nodes_count += 1
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_count += 1
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        docstring_count += 1
                elif isinstance(node, ast.ClassDef):
                    class_count += 1
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        docstring_count += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1
                elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                    assignment_count += 1
                elif isinstance(
                    node,
                    (
                        ast.If,
                        ast.For,
                        ast.AsyncFor,
                        ast.While,
                        ast.Try,
                        ast.With,
                        ast.AsyncWith,
                        ast.Match,
                    ),
                ):
                    control_flow_count += 1

            # Compute nesting & cyclomatic
            from app.analyzers.complexity import ComplexityAnalyzer
            comp_report = ComplexityAnalyzer.compute_complexity(ast_tree)
            max_nesting = comp_report.max_nesting_depth
            cyclomatic = comp_report.cyclomatic_complexity

        comment_ratio = round((comment_lines + docstring_count) / max(loc, 1), 3)
        avg_func_len = round(loc / max(function_count, 1), 1) if function_count > 0 else 0.0

        return CodeMetrics(
            lines_of_code=loc,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            average_function_length=avg_func_len,
            raw_character_count=raw_chars,
            ast_nodes_count=ast_nodes_count,
            variable_assignment_count=assignment_count,
            control_flow_node_count=control_flow_count,
            max_nesting_depth=max_nesting,
            cyclomatic_complexity=cyclomatic,
            comment_count=comment_lines,
            docstring_count=docstring_count,
            comment_ratio=comment_ratio,
        )
