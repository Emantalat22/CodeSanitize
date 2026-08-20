"""Provenance Comment & Linguistic Fingerprint Normalization Rule."""

import re
from typing import Any, List, Optional, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.provenance.comment_analyzer import (
    OBVIOUS_COMMENT_PATTERNS,
    is_preserved_developer_comment,
)
from app.transformers.base import BaseTransformationRule


class ProvCommentNormRule(BaseTransformationRule):
    """Normalizes and removes redundant generated-style comments and AI linguistic phrases while preserving developer notes."""

    @property
    def rule_id(self) -> str:
        return "PROV-COMMENT-NORM-01"

    @property
    def name(self) -> str:
        return "Linguistic & Comment Normalization"

    @property
    def description(self) -> str:
        return "Safely strips linguistic AI phrases and obvious comments while strictly preserving developer annotations, licenses, and TODOs."

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
        found_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                if is_preserved_developer_comment(stripped):
                    continue
                for comment_regex, _, _ in OBVIOUS_COMMENT_PATTERNS:
                    if re.match(comment_regex, stripped, re.IGNORECASE):
                        found_count += 1
                        break

        if found_count > 0:
            return True, f"Found {found_count} linguistic/generated AI comment pattern(s)."

        return False, "No redundant generated-style comments found."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        if not code or not code.strip():
            return code, ast_tree, "Empty source - no changes applied", 0

        lines = code.splitlines()
        new_lines = []
        removed_count = 0

        for line in lines:
            stripped = line.strip()
            should_remove = False

            if stripped.startswith("#") or stripped.startswith("//"):
                if not is_preserved_developer_comment(stripped):
                    for comment_regex, _, _ in OBVIOUS_COMMENT_PATTERNS:
                        if re.match(comment_regex, stripped, re.IGNORECASE):
                            should_remove = True
                            removed_count += 1
                            break

            if not should_remove:
                new_lines.append(line)

        modified_code = "\n".join(new_lines)
        if code.endswith("\n") and not modified_code.endswith("\n"):
            modified_code += "\n"

        details = f"Stripped {removed_count} linguistic AI phrase(s) and redundant comment(s)."
        return modified_code, None, details, removed_count
