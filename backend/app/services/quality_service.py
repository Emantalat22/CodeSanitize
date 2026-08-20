"""Deterministic Code Quality and Health Scoring Service."""

from typing import List
from app.models.schemas import (
    AnalysisFinding,
    CodeMetrics,
    ComplexityReport,
    FindingSeverity,
)


class QualityService:
    """Calculates deterministic, static-analysis-grade code quality scores (0-100)."""

    @classmethod
    def calculate_quality_score(
        cls,
        findings: List[AnalysisFinding],
        complexity: ComplexityReport,
        metrics: CodeMetrics,
    ) -> int:
        """Calculate holistic, realistic quality score (0-100).

        Scoring Rules:
        - Baseline: 95 points (100/100 is reserved only for fully docstringed, zero-debt, low-complexity code).
        - Maintainability:
          - Docstring / comment ratio < 0.15: -4 points
          - Docstring / comment ratio < 0.05: -8 points
          - Average function length > 30 lines: -4 points
          - Average function length > 50 lines: -8 points
        - Complexity:
          - Max cyclomatic complexity > 15: -12 points
          - Max cyclomatic complexity > 8: -6 points
          - Max cyclomatic complexity > 4: -2 points
          - Max nesting depth > 3: -(max_nesting_depth - 3) * 3 points
        - Security & Vulnerability Penalties:
          - CRITICAL: -30 points each
          - HIGH: -15 points each
          - MEDIUM: -8 points each
          - LOW: -3 points each
        """
        # Empty code baseline
        if metrics.lines_of_code == 0:
            return 0

        score = 95

        # 1. Maintainability adjustments
        if metrics.comment_ratio >= 0.25 and metrics.function_count > 0:
            score += 3  # Exceptional documentation bonus
        elif metrics.comment_ratio < 0.05:
            score -= 8
        elif metrics.comment_ratio < 0.15:
            score -= 4

        if metrics.average_function_length > 50:
            score -= 8
        elif metrics.average_function_length > 30:
            score -= 4

        # 2. Complexity penalties
        if complexity.maximum_complexity > 15:
            score -= 12
        elif complexity.maximum_complexity > 8:
            score -= 6
        elif complexity.maximum_complexity > 4:
            score -= 2

        if complexity.max_nesting_depth > 3:
            score -= (complexity.max_nesting_depth - 3) * 3

        # 3. Finding penalties
        for f in findings:
            if f.severity == FindingSeverity.CRITICAL:
                score -= 30
            elif f.severity == FindingSeverity.HIGH:
                score -= 15
            elif f.severity == FindingSeverity.MEDIUM:
                score -= 8
            elif f.severity == FindingSeverity.LOW:
                score -= 3

        # 4. Perfect 100 condition: only when zero findings, complexity <= 2, and high doc coverage
        if len(findings) == 0 and complexity.maximum_complexity <= 2 and metrics.comment_ratio >= 0.35:
            score = 100

        return max(min(score, 100), 0)
