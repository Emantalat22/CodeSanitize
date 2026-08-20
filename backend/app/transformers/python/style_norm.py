"""Provenance Style Normalization Rule."""

from typing import Any, List, Optional, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule


class ProvStyleNormRule(BaseTransformationRule):
    """Normalizes inconsistent generated style, trailing comment whitespace, and redundant line padding."""

    @property
    def rule_id(self) -> str:
        return "PROV-STYLE-NORM-01"

    @property
    def name(self) -> str:
        return "Provenance Style Normalization"

    @property
    def description(self) -> str:
        return "Standardizes whitespace padding, trailing inline noise, and blank line structures"

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [
            SupportedLanguage.PYTHON,
            SupportedLanguage.JAVASCRIPT,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVA,
            SupportedLanguage.CPP,
            SupportedLanguage.C,
            SupportedLanguage.GO,
            SupportedLanguage.RUST,
        ]

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        return TransformationSafetyLevel.SAFE_CONSERVATIVE

    @property
    def default_enabled(self) -> bool:
        return True

    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code or not code.strip():
            return False, "Code is empty."

        lines = code.splitlines()
        has_trailing = any(line != line.rstrip() for line in lines)
        blank_run = 0
        has_excessive_blanks = False
        for line in lines:
            if not line.strip():
                blank_run += 1
                if blank_run > 2:
                    has_excessive_blanks = True
                    break
            else:
                blank_run = 0

        if has_trailing or has_excessive_blanks:
            return True, "Found unnormalized trailing whitespace or excessive blank lines."

        return False, "Style formatting is already clean."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        if not code or not code.strip():
            return code, ast_tree, "Empty source - no changes applied", 0

        original_code = code

        # 1. Strip trailing whitespace from all lines
        lines = [line.rstrip() for line in code.splitlines()]

        # 2. Collapse excessive 3+ consecutive blank lines down to 2
        processed_lines = []
        blank_run = 0
        collapsed_count = 0
        for line in lines:
            if not line:
                blank_run += 1
                if blank_run <= 2:
                    processed_lines.append(line)
                else:
                    collapsed_count += 1
            else:
                blank_run = 0
                processed_lines.append(line)

        modified = "\n".join(processed_lines)
        if original_code.endswith("\n") and not modified.endswith("\n"):
            modified += "\n"

        diff_count = sum(1 for a, b in zip(original_code.splitlines(), modified.splitlines()) if a != b) + collapsed_count
        details = f"Normalized trailing whitespace and collapsed {collapsed_count} excessive blank lines."

        return modified, None, details, max(diff_count, 1)
