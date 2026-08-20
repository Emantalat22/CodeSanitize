"""Intelligent Static Code Recommendation Engine.

Synthesizes metrics, complexity bottlenecks, security vulnerabilities, and duplication findings
into prioritized, actionable refactoring and safety recommendations.
"""

from typing import List, Optional
from app.models.schemas import (
    AnalysisFinding,
    CodeMetrics,
    ComplexityReport,
    DuplicationFinding,
    FindingCategory,
    FindingSeverity,
    SecurityReport,
)


class RecommendationService:
    """Generates prioritized developer recommendations for code hygiene, security, and maintainability."""

    @classmethod
    def generate_recommendations(
        cls,
        findings: List[AnalysisFinding],
        complexity: Optional[ComplexityReport] = None,
        metrics: Optional[CodeMetrics] = None,
        security: Optional[SecurityReport] = None,
        duplications: Optional[List[DuplicationFinding]] = None,
    ) -> List[str]:
        """Generate deduplicated, prioritized list of recommendations."""
        recs: List[str] = []

        # 1. Critical Security Hardening Recommendations (Top Priority)
        sec_findings = [f for f in findings if f.category == FindingCategory.SECURITY]
        has_eval = any(f.id in ("SEC-EVAL-01", "SEC-EXEC-01") for f in sec_findings)
        if has_eval:
            recs.append(
                "Eliminate dynamic code execution (eval/exec); use ast.literal_eval() for data or static command dispatch."
            )

        has_shell = any(f.id in ("SEC-SUBPROCESS-SHELL-01", "SEC-CMD-INJECTION-01") for f in sec_findings)
        if has_shell:
            recs.append(
                "Prevent command injection by passing subprocess arguments as a list of strings [cmd, arg] with shell=False."
            )

        has_secrets = any("SECRET" in f.id or "PASSWORD" in f.id for f in sec_findings)
        if has_secrets:
            recs.append(
                "Externalize hardcoded credentials and API keys into environment variables (.env) or a secret manager."
            )

        has_weak_crypto = any("CRYPTO" in f.id for f in sec_findings)
        if has_weak_crypto:
            recs.append(
                "Upgrade broken hash algorithms (MD5/SHA-1) to cryptographically secure SHA-256 (hashlib.sha256()) or Argon2."
            )

        has_sql = any("SQL" in f.id for f in sec_findings)
        if has_sql:
            recs.append(
                "Avoid SQL string concatenation; use parameterized queries or an ORM to prevent SQL injection."
            )

        # 2. Complexity & Control-Flow Refactoring Recommendations
        if complexity:
            for fn in complexity.most_complex_functions:
                if fn.complexity > 10:
                    recs.append(
                        f"Refactor complex function '{fn.name}' (Cyclomatic Complexity={fn.complexity}, Nesting={fn.nesting_depth}) into smaller focused helper functions."
                    )
                elif fn.nesting_depth >= 4:
                    recs.append(
                        f"Flatten nested control structures in '{fn.name}' by adopting early return guard clauses."
                    )

        # 3. Maintainability & Code Sizing Recommendations
        if metrics:
            if metrics.average_function_length > 40:
                recs.append(
                    f"Functions average {metrics.average_function_length} lines; decompose oversized routines to improve readability and testability."
                )
            if metrics.comment_ratio < 0.05 and metrics.lines_of_code > 20:
                recs.append(
                    "Improve documentation density by adding docstrings and parameter type annotations to public interfaces."
                )

        # 4. Code Duplication & DRY Recommendations
        if duplications:
            count = len(duplications)
            if count > 0:
                recs.append(
                    f"Consolidate {count} detected code duplication(s) into shared reusable utility functions to adhere to DRY principles."
                )

        # 5. Extract additional recommendations directly from analyzer findings
        for f in findings:
            if f.recommendation and f.recommendation not in recs and len(recs) < 10:
                recs.append(f.recommendation)

        return recs
