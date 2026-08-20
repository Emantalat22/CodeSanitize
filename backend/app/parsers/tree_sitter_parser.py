"""Tree-sitter and unified multi-language parser adapter for JS, TS, Java, C++, C, Go, Rust, and others."""

from typing import Any, List, Optional, Tuple
from app.models.cir import IRProgram
from app.models.schemas import (
    AnalysisIssue,
    CodeMetrics,
    IssueSeverity,
    ParserCapabilities,
    SupportedLanguage,
)
from app.parsers.base import BaseLanguageParser
from app.parsers.cir_extractor import CIRExtractor

# Try importing tree_sitter and language modules safely
try:
    import tree_sitter as ts
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    ts = None
    _TREE_SITTER_AVAILABLE = False


def _get_tree_sitter_language(lang: SupportedLanguage) -> Optional[Any]:
    """Retrieve the compiled Tree-sitter Language object for a given language."""
    if not _TREE_SITTER_AVAILABLE:
        return None

    try:
        if lang == SupportedLanguage.JAVASCRIPT:
            import tree_sitter_javascript as tsjs
            return ts.Language(tsjs.language())
        elif lang == SupportedLanguage.TYPESCRIPT:
            import tree_sitter_typescript as tst
            return ts.Language(tst.language_typescript())
        elif lang == SupportedLanguage.JAVA:
            import tree_sitter_java as tsj
            return ts.Language(tsj.language())
        elif lang == SupportedLanguage.CPP:
            import tree_sitter_cpp as tscpp
            return ts.Language(tscpp.language())
        elif lang == SupportedLanguage.C:
            import tree_sitter_c as tsc
            return ts.Language(tsc.language())
        elif lang == SupportedLanguage.GO:
            import tree_sitter_go as tsgo
            return ts.Language(tsgo.language())
        elif lang == SupportedLanguage.RUST:
            import tree_sitter_rust as tsrs
            return ts.Language(tsrs.language())
    except Exception:
        return None
    return None


class TreeSitterParser(BaseLanguageParser[Any]):
    """Generic Tree-sitter AST and unified CIR parser for multi-language source analysis."""

    def __init__(self, language: SupportedLanguage, display_name: str):
        self._language = language
        self._display_name = display_name
        self._ts_language = _get_tree_sitter_language(language)
        self._parser = None
        if self._ts_language is not None:
            try:
                self._parser = ts.Parser(self._ts_language)
            except Exception:
                self._parser = None

    @property
    def language(self) -> SupportedLanguage:
        return self._language

    @property
    def parser_name(self) -> str:
        if self._parser is not None:
            return f"Tree-sitter {self._display_name}"
        return f"Unified CIR Parser ({self._display_name})"

    def is_available(self) -> bool:
        # The parser is always functional via Tree-sitter or the Common IR extractor
        return True

    def get_capabilities(self) -> ParserCapabilities:
        has_ts = self._parser is not None
        return ParserCapabilities(
            ast_available=True,
            syntax_validation=True,
            metrics_collection=True,
            non_functional_detection=True,
            engine_name=f"Tree-sitter ({self._display_name})" if has_ts else f"Unified CIR ({self._display_name})",
        )

    def parse(self, code: str) -> Tuple[Optional[Any], List[AnalysisIssue]]:
        """Parse code into a Tree-sitter CST or Common IR representation."""
        issues: List[AnalysisIssue] = []

        if self._parser is not None:
            try:
                code_bytes = code.encode("utf-8")
                tree = self._parser.parse(code_bytes)

                # Check for syntax errors in Tree-sitter CST
                if tree.root_node.has_error:
                    issues.append(
                        AnalysisIssue(
                            rule_id="TS-SYNTAX-ERROR",
                            message=f"Syntax error detected in {self._display_name} source code.",
                            severity=IssueSeverity.ERROR,
                            line_start=1,
                        )
                    )

                return tree, issues
            except Exception as e:
                issues.append(
                    AnalysisIssue(
                        rule_id="TS-PARSE-EXCEPTION",
                        message=f"Parser encountered an error: {str(e)}",
                        severity=IssueSeverity.WARNING,
                    )
                )

        # Fallback to Unified Common IR AST
        cir = CIRExtractor.extract(code, self._language, None)
        return cir, issues

    def collect_metrics(self, code: str, ast: Optional[Any]) -> CodeMetrics:
        """Calculate language-agnostic structural metrics."""
        lines = code.splitlines() if code else []
        loc = len(lines)
        raw_chars = len(code)

        if isinstance(ast, IRProgram):
            cir = ast
        else:
            cir = CIRExtractor.extract(code, self._language, ast)

        function_count = len(cir.functions)
        class_count = len(cir.classes)
        import_count = len(cir.imports)
        control_flow_count = len(cir.control_flows)
        blank_lines = cir.blank_lines
        comment_lines = cir.comment_lines
        cyclomatic = cir.total_cyclomatic_complexity

        comment_ratio = round(comment_lines / max(loc, 1), 3)
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
            ast_nodes_count=max(loc * 3, 10),
            control_flow_node_count=control_flow_count,
            max_nesting_depth=cir.max_nesting_depth,
            cyclomatic_complexity=cyclomatic,
            comment_count=comment_lines,
            docstring_count=0,
            comment_ratio=comment_ratio,
        )
