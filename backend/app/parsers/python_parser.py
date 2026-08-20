"""Production-grade Python AST and token parser implementation."""

import ast
import io
import tokenize
from typing import List, Optional, Tuple
from app.models.schemas import (
    AnalysisIssue,
    IssueSeverity,
    ParserCapabilities,
    StructuralMetrics,
    SupportedLanguage,
)
from app.parsers.base import BaseLanguageParser


class PythonNestingVisitor(ast.NodeVisitor):
    """AST visitor to compute maximum statement nesting depth."""

    def __init__(self):
        self.current_depth = 0
        self.max_depth = 0

    def _visit_nested_block(self, node: ast.AST):
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_nested_block(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_nested_block(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._visit_nested_block(node)

    def visit_If(self, node: ast.If):
        self._visit_nested_block(node)

    def visit_For(self, node: ast.For):
        self._visit_nested_block(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._visit_nested_block(node)

    def visit_While(self, node: ast.While):
        self._visit_nested_block(node)

    def visit_Try(self, node: ast.Try):
        self._visit_nested_block(node)

    def visit_With(self, node: ast.With):
        self._visit_nested_block(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._visit_nested_block(node)

    def visit_Match(self, node: ast.Match):
        self._visit_nested_block(node)


class PythonParser(BaseLanguageParser[ast.AST]):
    """Python AST and token-based code parser."""

    @property
    def language(self) -> SupportedLanguage:
        return SupportedLanguage.PYTHON

    @property
    def parser_name(self) -> str:
        return "Python Built-in AST & Tokenizer"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self) -> ParserCapabilities:
        return ParserCapabilities(
            ast_available=True,
            syntax_validation=True,
            metrics_collection=True,
            non_functional_detection=True,
            engine_name="Python standard ast & tokenize",
        )

    def parse(self, code: str) -> Tuple[Optional[ast.AST], List[AnalysisIssue]]:
        """Parse Python source code into an AST without execution."""
        issues: List[AnalysisIssue] = []
        if not code.strip():
            # Empty code is syntactically valid in Python
            try:
                tree = ast.parse("", filename="<input>")
                return tree, issues
            except Exception as e:
                issues.append(
                    AnalysisIssue(
                        rule_id="PY-PARSE-ERROR",
                        message=f"Failed to parse empty source: {str(e)}",
                        severity=IssueSeverity.ERROR,
                    )
                )
                return None, issues

        try:
            tree = ast.parse(code, filename="<input>")
            return tree, issues
        except SyntaxError as err:
            issues.append(
                AnalysisIssue(
                    rule_id="PY-SYNTAX-ERROR",
                    message=err.msg or "Syntax error in Python source code",
                    severity=IssueSeverity.ERROR,
                    line_start=err.lineno,
                    line_end=err.end_lineno or err.lineno,
                    column_start=err.offset,
                    column_end=err.end_offset or err.offset,
                    metadata={
                        "text": err.text.strip() if err.text else None,
                        "filename": err.filename,
                    },
                )
            )
            return None, issues
        except Exception as err:
            issues.append(
                AnalysisIssue(
                    rule_id="PY-PARSE-ERROR",
                    message=f"Parser exception: {str(err)}",
                    severity=IssueSeverity.ERROR,
                )
            )
            return None, issues

    def collect_metrics(self, code: str, parsed_ast: Optional[ast.AST]) -> StructuralMetrics:
        """Collect metrics from Python AST and token stream."""
        lines = code.splitlines()
        line_count = len(lines) if code else 0
        raw_char_count = len(code)

        comment_count = 0
        docstring_count = 0

        # Extract comments and tokenize safely
        try:
            tokens = tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    comment_count += 1
        except Exception:
            # Tokenizer error on malformed tokens; fallback to line scanning
            comment_count = sum(1 for line in lines if line.strip().startswith("#"))

        if parsed_ast is None:
            return StructuralMetrics(
                lines_of_code=line_count,
                raw_character_count=raw_char_count,
                ast_nodes_count=0,
                function_count=0,
                class_count=0,
                import_count=0,
                variable_assignment_count=0,
                control_flow_node_count=0,
                max_nesting_depth=0,
                cyclomatic_complexity=1,
                comment_count=comment_count,
                docstring_count=0,
            )

        ast_node_count = 0
        function_count = 0
        class_count = 0
        import_count = 0
        var_assign_count = 0
        control_flow_count = 0
        cyclomatic_complexity = 1  # Base complexity

        # Check for module docstring
        if ast.get_docstring(parsed_ast):
            docstring_count += 1

        for node in ast.walk(parsed_ast):
            ast_node_count += 1

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1
                if ast.get_docstring(node):
                    docstring_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
                if ast.get_docstring(node):
                    docstring_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                var_assign_count += 1

            # Control flow and complexity points
            if isinstance(node, (ast.If, ast.IfExp)):
                control_flow_count += 1
                cyclomatic_complexity += 1
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                control_flow_count += 1
                cyclomatic_complexity += 1
            elif isinstance(node, ast.While):
                control_flow_count += 1
                cyclomatic_complexity += 1
            elif isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                control_flow_count += 1
            elif isinstance(node, ast.ExceptHandler):
                cyclomatic_complexity += 1
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                control_flow_count += 1
            elif isinstance(node, ast.Match):
                control_flow_count += 1
            elif isinstance(node, ast.match_case):
                cyclomatic_complexity += 1
            elif isinstance(node, ast.BoolOp):
                # Each 'and' / 'or' condition adds a branch
                cyclomatic_complexity += max(len(node.values) - 1, 1)

        # Compute maximum nesting depth
        visitor = PythonNestingVisitor()
        visitor.visit(parsed_ast)
        max_nesting = visitor.max_depth

        return StructuralMetrics(
            lines_of_code=line_count,
            raw_character_count=raw_char_count,
            ast_nodes_count=ast_node_count,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            variable_assignment_count=var_assign_count,
            control_flow_node_count=control_flow_count,
            max_nesting_depth=max_nesting,
            cyclomatic_complexity=cyclomatic_complexity,
            comment_count=comment_count,
            docstring_count=docstring_count,
        )
