"""Common Intermediate Representation (CIR) Extractor.

Converts Python AST, Tree-sitter CSTs, and multi-language source code into
a unified IRProgram representation for language-agnostic static analysis.
"""

import ast
import re
from typing import Any, List, Optional
from app.models.cir import (
    IRAssignment,
    IRCall,
    IRClass,
    IRComment,
    IRControlFlow,
    IRFunction,
    IRImport,
    IRParameter,
    IRProgram,
)
from app.models.schemas import SupportedLanguage


class CIRExtractor:
    """Extracts unified IRProgram AST models from language-specific parse trees."""

    @classmethod
    def extract(
        cls,
        code: str,
        language: SupportedLanguage,
        ast_tree: Optional[Any] = None,
    ) -> IRProgram:
        """Extract language-agnostic IRProgram model."""
        lines = code.splitlines() if code else []
        loc = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())

        if language == SupportedLanguage.PYTHON and isinstance(ast_tree, ast.AST):
            return cls._extract_python(code, ast_tree, loc, blank_lines)
        elif ast_tree is not None and hasattr(ast_tree, "root_node"):
            return cls._extract_tree_sitter(code, language, ast_tree, loc, blank_lines)
        else:
            return cls._extract_structural_heuristics(code, language, loc, blank_lines)

    @classmethod
    def _extract_python(
        cls, code: str, tree: ast.AST, loc: int, blank_lines: int
    ) -> IRProgram:
        """Extract CIR model from native Python AST."""
        functions: List[IRFunction] = []
        classes: List[IRClass] = []
        imports: List[IRImport] = []
        control_flows: List[IRControlFlow] = []
        assignments: List[IRAssignment] = []
        calls: List[IRCall] = []
        comments: List[IRComment] = []

        # Comments
        for idx, line in enumerate(code.splitlines(), start=1):
            trimmed = line.strip()
            if trimmed.startswith("#"):
                comments.append(IRComment(text=trimmed, is_docstring=False, line_start=idx))

        # AST nodes
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        IRImport(
                            module_name=alias.name,
                            alias=alias.asname,
                            line_start=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                syms = [a.name for a in node.names]
                imports.append(
                    IRImport(
                        module_name=mod,
                        imported_symbols=syms,
                        is_relative=(node.level or 0) > 0,
                        line_start=node.lineno,
                    )
                )

            # Classes
            elif isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) if hasattr(ast, "unparse") else getattr(b, "id", "") for b in node.bases]
                doc = None
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    doc = node.body[0].value.value

                classes.append(
                    IRClass(
                        name=node.name,
                        class_type="class",
                        bases=bases,
                        docstring=doc,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno) or node.lineno,
                    )
                )

            # Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [IRParameter(name=arg.arg) for arg in node.args.args]
                doc = None
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    doc = node.body[0].value.value

                fn_calls: List[IRCall] = []
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        c_name = ast.unparse(sub.func) if hasattr(ast, "unparse") else ""
                        fn_calls.append(
                            IRCall(
                                callee_name=c_name,
                                arguments_count=len(sub.args),
                                line_start=sub.lineno,
                                is_eval_or_exec=c_name in ("eval", "exec"),
                                is_subprocess="subprocess" in c_name or "os.system" in c_name,
                            )
                        )

                # Local complexity
                fn_comp = 1
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.If, ast.For, ast.AsyncFor, ast.While)):
                        fn_comp += 1
                    elif isinstance(sub, ast.Try):
                        fn_comp += len(sub.handlers)

                functions.append(
                    IRFunction(
                        name=node.name,
                        parameters=params,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno) or node.lineno,
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        docstring=doc,
                        statement_count=len(node.body),
                        cyclomatic_complexity=fn_comp,
                        calls=fn_calls,
                    )
                )

            # Control Flow
            elif isinstance(node, ast.If):
                control_flows.append(IRControlFlow(kind="if", line_start=node.lineno, branch_count=2))
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                control_flows.append(IRControlFlow(kind="loop", line_start=node.lineno))
            elif isinstance(node, ast.Try):
                control_flows.append(
                    IRControlFlow(
                        kind="try_catch",
                        line_start=node.lineno,
                        branch_count=len(node.handlers) + 1,
                    )
                )

            # Assignments
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                assignments.append(IRAssignment(target_name="var", is_declaration=True, line_start=node.lineno))

            # Calls
            elif isinstance(node, ast.Call):
                c_name = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
                calls.append(
                    IRCall(
                        callee_name=c_name,
                        arguments_count=len(node.args),
                        line_start=node.lineno,
                        is_eval_or_exec=c_name in ("eval", "exec"),
                        is_subprocess="subprocess" in c_name or "os.system" in c_name,
                    )
                )

        total_comp = 1 + len(control_flows)

        return IRProgram(
            language=SupportedLanguage.PYTHON,
            lines_of_code=loc,
            blank_lines=blank_lines,
            comment_lines=len(comments),
            functions=functions,
            classes=classes,
            imports=imports,
            control_flows=control_flows,
            assignments=assignments,
            calls=calls,
            comments=comments,
            total_cyclomatic_complexity=total_comp,
        )

    @classmethod
    def _extract_tree_sitter(
        cls, code: str, language: SupportedLanguage, ts_tree: Any, loc: int, blank_lines: int
    ) -> IRProgram:
        """Extract CIR model from Tree-sitter CST."""
        functions: List[IRFunction] = []
        classes: List[IRClass] = []
        imports: List[IRImport] = []
        control_flows: List[IRControlFlow] = []
        calls: List[IRCall] = []
        comments: List[IRComment] = []

        code_bytes = code.encode("utf-8")

        def _get_text(node: Any) -> str:
            return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

        def _traverse(node: Any):
            node_type = node.type

            # Functions & Methods
            if node_type in (
                "function_declaration",
                "function_definition",
                "method_declaration",
                "method_definition",
                "arrow_function",
                "function_item",
            ):
                fn_name = "anonymous"
                for child in node.children:
                    if child.type in ("identifier", "name", "field_identifier"):
                        fn_name = _get_text(child)
                        break

                functions.append(
                    IRFunction(
                        name=fn_name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        statement_count=len(node.children),
                    )
                )

            # Classes & Structs
            elif node_type in (
                "class_declaration",
                "class_definition",
                "class_specifier",
                "struct_item",
                "struct_specifier",
                "interface_declaration",
                "type_declaration",
            ):
                cls_name = "AnonymousClass"
                for child in node.children:
                    if child.type in ("type_identifier", "identifier", "name"):
                        cls_name = _get_text(child)
                        break

                classes.append(
                    IRClass(
                        name=cls_name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                )


            # Imports
            elif node_type in (
                "import_statement",
                "import_declaration",
                "use_declaration",
                "preproc_include",
                "include_statement",
            ):
                imports.append(
                    IRImport(
                        module_name=_get_text(node).strip()[:40],
                        line_start=node.start_point[0] + 1,
                    )
                )

            # Control Flow
            elif node_type in ("if_statement", "if_expression"):
                control_flows.append(IRControlFlow(kind="if", line_start=node.start_point[0] + 1))
            elif node_type in ("for_statement", "for_expression", "while_statement", "while_expression", "loop_expression"):
                control_flows.append(IRControlFlow(kind="loop", line_start=node.start_point[0] + 1))
            elif node_type in ("try_statement", "catch_clause", "match_expression"):
                control_flows.append(IRControlFlow(kind="try_catch", line_start=node.start_point[0] + 1))

            # Calls
            elif node_type in ("call_expression", "method_invocation", "function_call"):
                c_text = _get_text(node)
                calls.append(
                    IRCall(
                        callee_name=c_text[:30],
                        line_start=node.start_point[0] + 1,
                        is_eval_or_exec="eval(" in c_text or "exec(" in c_text,
                    )
                )

            # Comments
            elif "comment" in node_type:
                comments.append(
                    IRComment(
                        text=_get_text(node),
                        line_start=node.start_point[0] + 1,
                    )
                )

            for child in node.children:
                _traverse(child)

        _traverse(ts_tree.root_node)

        total_comp = 1 + len(control_flows)

        return IRProgram(
            language=language,
            lines_of_code=loc,
            blank_lines=blank_lines,
            comment_lines=len(comments),
            functions=functions,
            classes=classes,
            imports=imports,
            control_flows=control_flows,
            calls=calls,
            comments=comments,
            total_cyclomatic_complexity=total_comp,
        )

    @classmethod
    def _extract_structural_heuristics(
        cls, code: str, language: SupportedLanguage, loc: int, blank_lines: int
    ) -> IRProgram:
        """Universal fallback scanner for any programming language."""
        lines = code.splitlines() if code else []
        functions: List[IRFunction] = []
        classes: List[IRClass] = []
        imports: List[IRImport] = []
        control_flows: List[IRControlFlow] = []
        calls: List[IRCall] = []
        comments: List[IRComment] = []

        fn_patterns = [
            r"\bfunc\s+(\([^\)]+\)\s*)?([a-zA-Z_]\w*)\s*\(",  # Go
            r"\bfn\s+([a-zA-Z_]\w*)\s*\(",                   # Rust
            r"\bfunction\s+([a-zA-Z_]\w*)\s*\(",             # JS/PHP
            r"\bpublic\s+(?:static\s+)?(?:[\w<>\[\]]+\s+)+([a-zA-Z_]\w*)\s*\(",  # Java/C#
            r"(?:[\w:*&<>]+\s+)+([a-zA-Z_]\w*)\s*\([^;]*?\)\s*\{",  # C/C++
        ]

        cls_patterns = [
            r"\bclass\s+([a-zA-Z_]\w*)",
            r"\bstruct\s+([a-zA-Z_]\w*)",
            r"\binterface\s+([a-zA-Z_]\w*)",
            r"\btype\s+([a-zA-Z_]\w*)\s+struct",
            r"\bimpl\s+(?:<[^>]+>\s*)?([a-zA-Z_]\w*)",
        ]

        imp_patterns = [
            r"#include\s+[<\"][^>\"]+[>\"]",
            r"\bimport\s+[^;]+",
            r"\buse\s+[^;]+",
            r"\bpackage\s+\w+",
            r"\busing\s+[^;]+",
        ]

        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if not trimmed:
                continue

            # Comments
            if trimmed.startswith(("//", "#", "/*", "*")):
                comments.append(IRComment(text=trimmed, line_start=idx))
                continue

            # Imports
            for pat in imp_patterns:
                if re.search(pat, trimmed):
                    imports.append(IRImport(module_name=trimmed[:40], line_start=idx))
                    break

            # Classes
            for pat in cls_patterns:
                m = re.search(pat, trimmed)
                if m:
                    classes.append(IRClass(name=m.group(1), line_start=idx))
                    break

            # Functions
            for pat in fn_patterns:
                m = re.search(pat, trimmed)
                if m:
                    fn_name = m.group(m.lastindex) if m.lastindex else "fn"
                    functions.append(IRFunction(name=fn_name, line_start=idx))
                    break

            # Control flow
            if re.search(r"\bif\s*\(|\bif\s+[^{]+", trimmed):
                control_flows.append(IRControlFlow(kind="if", line_start=idx))
            elif re.search(r"\bfor\s*\(|\bfor\s+[^{]+|\bwhile\s*\(", trimmed):
                control_flows.append(IRControlFlow(kind="loop", line_start=idx))
            elif re.search(r"\btry\s*\{|\bcatch\s*\(|\bexcept\b", trimmed):
                control_flows.append(IRControlFlow(kind="try_catch", line_start=idx))

            # Calls
            if "eval(" in trimmed or "exec(" in trimmed:
                calls.append(IRCall(callee_name="eval", line_start=idx, is_eval_or_exec=True))
            if "subprocess" in trimmed or "os.system" in trimmed or "exec.Command" in trimmed:
                calls.append(IRCall(callee_name="subprocess", line_start=idx, is_subprocess=True))

        total_comp = 1 + len(control_flows)

        return IRProgram(
            language=language,
            lines_of_code=loc,
            blank_lines=blank_lines,
            comment_lines=len(comments),
            functions=functions,
            classes=classes,
            imports=imports,
            control_flows=control_flows,
            calls=calls,
            comments=comments,
            total_cyclomatic_complexity=total_comp,
        )
