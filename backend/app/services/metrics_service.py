"""Centralized metrics collection, complexity calculation, and score evaluation service."""

import ast
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import (
    AnalysisFinding,
    ComplexityFunctionMetric,
    ComplexityMetrics,
    FindingSeverity,
    StructuralMetrics,
)


class FunctionComplexityVisitor(ast.NodeVisitor):
    """Calculates McCabe cyclomatic complexity, nesting depth, and statement counts per function."""

    def __init__(self, func_name: str, line_start: int):
        self.func_name = func_name
        self.line_start = line_start
        self.complexity = 1
        self.max_nesting = 1
        self.current_nesting = 1
        self.statement_count = 0

    def _enter_block(self):
        self.current_nesting += 1
        if self.current_nesting > self.max_nesting:
            self.max_nesting = self.current_nesting

    def _exit_block(self):
        self.current_nesting -= 1

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_IfExp(self, node: ast.IfExp):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.complexity += 1
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_With(self, node: ast.With):
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.statement_count += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_BoolOp(self, node: ast.BoolOp):
        # Each boolean 'and' / 'or' condition adds to decision branches
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Match(self, node: Any):
        # Pattern match statement
        if hasattr(node, "cases"):
            self.complexity += len(node.cases)
        self.statement_count += 1
        self.generic_visit(node)


class MetricsService:
    """Central service calculating LOC, complexity, structural ratios, and quality scores."""

    @classmethod
    def calculate_complexity_metrics(cls, tree: Optional[ast.AST]) -> ComplexityMetrics:
        """Calculate detailed McCabe cyclomatic complexity and per-function breakdown."""
        if tree is None:
            return ComplexityMetrics()

        branching_count = 0
        loop_count = 0
        max_nesting = 0
        exception_count = 0
        function_metrics: List[ComplexityFunctionMetric] = []

        total_module_complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp)):
                branching_count += 1
                total_module_complexity += 1
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                loop_count += 1
                total_module_complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                exception_count += 1
                total_module_complexity += 1
            elif hasattr(ast, "Match") and isinstance(node, ast.Match):
                if hasattr(node, "cases"):
                    branching_count += len(node.cases)
                    total_module_complexity += len(node.cases)

        # Analyze top-level and method functions
        for node in tree.body if hasattr(tree, "body") else []:
            funcs_to_inspect: List[Tuple[Any, Optional[str]]] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs_to_inspect.append((node, None))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        funcs_to_inspect.append((item, node.name))

            for func_node, class_name in funcs_to_inspect:
                func_display = f"{class_name}.{func_node.name}" if class_name else func_node.name
                visitor = FunctionComplexityVisitor(func_display, getattr(func_node, "lineno", 1))
                for stmt in func_node.body:
                    visitor.visit(stmt)

                if visitor.max_nesting > max_nesting:
                    max_nesting = visitor.max_nesting

                function_metrics.append(
                    ComplexityFunctionMetric(
                        name=func_display,
                        line_start=visitor.line_start,
                        cyclomatic_complexity=visitor.complexity,
                        nesting_depth=visitor.max_nesting,
                        statement_count=visitor.statement_count,
                    )
                )

        return ComplexityMetrics(
            cyclomatic_complexity=total_module_complexity,
            branching_count=branching_count,
            loop_count=loop_count,
            max_nesting_depth=max_nesting,
            exception_handling_count=exception_count,
            function_complexities=function_metrics,
        )

    @classmethod
    def calculate_structural_metrics(
        cls, code: str, tree: Optional[ast.AST]
    ) -> StructuralMetrics:
        """Calculate complete structural statistics and ratios."""
        lines = code.splitlines()
        loc = len(lines)
        raw_chars = len(code)

        comment_count = 0
        docstring_count = 0

        if tree is not None:
            # Docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        docstring_count += 1

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                comment_count += 1

        comment_ratio = round((comment_count + docstring_count) / max(loc, 1), 3)

        function_count = 0
        class_count = 0
        import_count = 0
        assignment_count = 0
        control_flow_count = 0
        ast_nodes_count = 0

        if tree is not None:
            for node in ast.walk(tree):
                ast_nodes_count += 1
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_count += 1
                elif isinstance(node, ast.ClassDef):
                    class_count += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1
                elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                    assignment_count += 1
                elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)):
                    control_flow_count += 1

        avg_func_len = round(loc / max(function_count, 1), 1) if function_count > 0 else 0.0

        complexity = cls.calculate_complexity_metrics(tree)

        return StructuralMetrics(
            lines_of_code=loc,
            raw_character_count=raw_chars,
            ast_nodes_count=ast_nodes_count,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            variable_assignment_count=assignment_count,
            control_flow_node_count=control_flow_count,
            max_nesting_depth=complexity.max_nesting_depth,
            cyclomatic_complexity=complexity.cyclomatic_complexity,
            comment_count=comment_count,
            docstring_count=docstring_count,
            comment_ratio=comment_ratio,
            average_function_length=avg_func_len,
        )

    @classmethod
    def calculate_overall_score(
        cls,
        findings: List[AnalysisFinding],
        complexity: ComplexityMetrics,
        structural: StructuralMetrics,
    ) -> int:
        """Calculate holistic health & quality score (0-100)."""
        score = 100

        # Penalties for security and quality findings
        for f in findings:
            if f.severity == FindingSeverity.CRITICAL:
                score -= 25
            elif f.severity == FindingSeverity.HIGH:
                score -= 15
            elif f.severity == FindingSeverity.MEDIUM:
                score -= 8
            elif f.severity == FindingSeverity.LOW:
                score -= 3

        # Complexity penalties
        for fn in complexity.function_complexities:
            if fn.cyclomatic_complexity > 15:
                score -= 10
            elif fn.cyclomatic_complexity > 8:
                score -= 5

        # Nesting depth penalty
        if complexity.max_nesting_depth > 4:
            score -= (complexity.max_nesting_depth - 4) * 4

        return max(min(score, 100), 0)
