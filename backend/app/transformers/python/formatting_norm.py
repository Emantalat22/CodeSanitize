"""Formatting normalization rule for Python source code."""

from typing import Any, List, Optional, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule


class FormattingNormalizationRule(BaseTransformationRule):
    """Conservative formatting normalization rule.

    Normalizes:
    - Trailing whitespace on all lines.
    - Excessive blank lines (collapses 3+ consecutive empty lines into 2).
    - Line endings to standard Unix newlines ('\\n').
    - Ensures single trailing newline at the end of the file.
    """

    @property
    def rule_id(self) -> str:
        return "PY-FMT-NORM-01"

    @property
    def name(self) -> str:
        return "Formatting Normalization"

    @property
    def description(self) -> str:
        return (
            "Normalizes trailing whitespace, collapses excessive blank line clusters, "
            "and standardizes newline terminations without modifying code tokens."
        )

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

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        return TransformationSafetyLevel.SAFE_CONSERVATIVE

    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code:
            return False, "Code is empty."

        lines = code.split("\n")
        has_trailing_ws = any(line.endswith(" ") or line.endswith("\t") for line in lines)
        has_cr = "\r" in code

        # Check for 3+ consecutive blank lines
        has_excessive_blanks = False
        consecutive_blanks = 0
        for line in lines:
            if not line.strip():
                consecutive_blanks += 1
                if consecutive_blanks >= 3:
                    has_excessive_blanks = True
                    break
            else:
                consecutive_blanks = 0

        has_bad_eof = not code.endswith("\n") or code.endswith("\n\n")

        if has_trailing_ws or has_cr or has_excessive_blanks or has_bad_eof:
            return True, "Formatting anomalies (trailing whitespace, excessive blanks, or line endings) detected."

        return False, "Formatting is already normalized."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        if not code:
            return code, ast_tree, "Empty code - no changes applied", 0

        # Standardize line endings to \n
        normalized_newlines = code.replace("\r\n", "\n").replace("\r", "\n")
        raw_lines = normalized_newlines.split("\n")

        # 1. Strip trailing whitespace on each line
        stripped_lines: List[str] = [line.rstrip(" \t") for line in raw_lines]

        # 2. Collapse runs of >= 3 consecutive blank lines into 2 blank lines
        collapsed_lines: List[str] = []
        consecutive_blanks = 0
        collapsed_count = 0
        trailing_ws_count = sum(
            1 for orig, stripped in zip(raw_lines, stripped_lines) if orig != stripped
        )

        for line in stripped_lines:
            if not line:
                consecutive_blanks += 1
                if consecutive_blanks <= 2:
                    collapsed_lines.append(line)
                else:
                    collapsed_count += 1
            else:
                consecutive_blanks = 0
                collapsed_lines.append(line)

        # 3. Ensure single trailing newline
        new_code = "\n".join(collapsed_lines).rstrip("\n") + "\n"
        if new_code.strip() == "":
            new_code = ""

        total_changes = trailing_ws_count + collapsed_count
        if new_code != code and total_changes == 0:
            total_changes = 1

        details = (
            f"Normalized formatting: removed trailing whitespace on {trailing_ws_count} line(s), "
            f"collapsed {collapsed_count} excessive blank line(s), standardized newline endings."
        )

        return new_code, None, details, total_changes
