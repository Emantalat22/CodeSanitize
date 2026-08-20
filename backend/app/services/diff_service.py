"""Diff generation and metrics service."""

import difflib
from typing import Optional, Tuple
from app.models.schemas import DiffSummary


class DiffService:
    """Service providing unified diff generation and statistics."""

    @staticmethod
    def generate_unified_diff(
        original_code: str,
        transformed_code: str,
        filename: Optional[str] = None,
    ) -> Tuple[Optional[str], DiffSummary]:
        """Generate a unified diff and calculate insertion/deletion statistics.

        Args:
            original_code: Original source text.
            transformed_code: Transformed source text.
            filename: Virtual filename for diff headers.

        Returns:
            Tuple of (unified_diff_string, DiffSummary).
        """
        if original_code == transformed_code:
            return None, DiffSummary(additions=0, removals=0, changed_lines=0)

        orig_lines = original_code.splitlines(keepends=True)
        trans_lines = transformed_code.splitlines(keepends=True)

        file_label = filename or "source_code"
        diff_lines = list(
            difflib.unified_diff(
                orig_lines,
                trans_lines,
                fromfile=f"a/{file_label}",
                tofile=f"b/{file_label}",
                lineterm="",
            )
        )

        if not diff_lines:
            return None, DiffSummary(additions=0, removals=0, changed_lines=0)

        additions = 0
        removals = 0

        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                removals += 1

        changed_lines = max(additions, removals)
        diff_text = "\n".join(diff_lines)

        return diff_text, DiffSummary(
            additions=additions,
            removals=removals,
            changed_lines=changed_lines,
        )
