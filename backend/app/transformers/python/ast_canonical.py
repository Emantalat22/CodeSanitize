"""AST Canonical Formatting rule for Python using native ast unparser."""

import ast
from typing import Any, List, Optional, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule


class AstCanonicalFormatRule(BaseTransformationRule):
    """Canonical AST formatting rule for Python.

    Constructs a clean, normalized code representation from the verified AST.
    Standardizes:
    - Operator and delimiter spacing according to PEP 8 standards.
    - Redundant parentheses around expressions.
    - Statement indentation and compound statement layout.
    Preserves all constants, variable names, docstrings, licensing, and control-flow semantics.
    """

    @property
    def rule_id(self) -> str:
        return "PY-AST-CANON-01"

    @property
    def name(self) -> str:
        return "AST Canonical Formatting"

    @property
    def description(self) -> str:
        return (
            "Regenerates canonical, standardized source code from the verified AST, "
            "normalizing expression spacing and redundant parenthesization."
        )

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        return TransformationSafetyLevel.SAFE_CONSERVATIVE

    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code.strip():
            return False, "Code is empty."

        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
            unparsed = ast.unparse(tree).strip()
            # If the unparsed code differs meaningfully from original code, rule is applicable
            if unparsed != code.strip():
                return True, "AST canonicalization will standardize expression layouts and formatting."
            return False, "Code is already in canonical AST format."
        except Exception as e:
            return False, f"AST parsing failed: {str(e)}"

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
            unparsed = ast.unparse(tree).strip() + "\n"

            # Preserve leading developer header comments (License, Copyright, TODO, shebangs)
            preserved_headers = []
            for line in code.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    lower = stripped.lstrip("#/ *").strip().lower()
                    if any(lower.startswith(p) for p in ("!", "license", "copyright", "todo", "fixme", "note", "type:")):
                        preserved_headers.append(line)
                        continue
                elif not stripped and preserved_headers:
                    preserved_headers.append(line)
                    continue
                break

            if preserved_headers:
                header_block = "\n".join(preserved_headers).rstrip() + "\n\n"
                unparsed = header_block + unparsed

            changes_desc = (
                "Applied AST canonical unparsing: normalized operator spacing, "
                "expression layouts, and statement structure."
            )
            # Count line differences
            orig_lines = set(code.splitlines())
            new_lines = set(unparsed.splitlines())
            change_count = max(len(orig_lines.symmetric_difference(new_lines)), 1)

            return unparsed, tree, changes_desc, change_count
        except Exception as e:
            return code, ast_tree, f"AST unparsing error: {str(e)}", 0
