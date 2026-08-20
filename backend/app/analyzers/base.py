"""Base abstract interface for CodeSanitize static analyzer modules."""

from abc import ABC, abstractmethod
import ast
import time
from typing import Any, Dict, List, Optional
from app.models.schemas import (
    AnalysisFinding,
    AnalyzerReport,
    StructuralMetrics,
    SupportedLanguage,
)


class BaseAnalyzer(ABC):
    """Abstract base class for static code intelligence analyzers.

    All analyzers must:
    - Have a unique ID and human-readable metadata.
    - Declare supported languages.
    - Operate strictly read-only without modifying source code or executing it.
    - Return structured AnalyzerReport with AnalysisFinding records.
    """

    @property
    @abstractmethod
    def analyzer_id(self) -> str:
        """Unique identifier (e.g. ANLZ-QUAL-01, ANLZ-SEC-01)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable analyzer name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of analysis capabilities."""
        pass

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        """List of supported programming languages (default: all)."""
        return [SupportedLanguage.PYTHON]

    def run(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Optional[Dict[str, Any]] = None,
    ) -> AnalyzerReport:
        """Execute analyzer with timing and error isolation."""
        options = options or {}
        start_time = time.perf_counter()

        try:
            findings = self.analyze(code, ast_tree, metrics, options)
            status = "completed"
        except Exception as e:
            findings = [
                AnalysisFinding(
                    id=f"{self.analyzer_id}-ERR",
                    category="quality",  # type: ignore
                    severity="info",  # type: ignore
                    title="Analyzer execution note",
                    description=f"Analyzer encountered a non-fatal error during inspection: {str(e)}",
                )
            ]
            status = "partial"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return AnalyzerReport(
            analyzer_id=self.analyzer_id,
            analyzer_name=self.name,
            execution_time_ms=elapsed_ms,
            status=status,
            findings_count=len(findings),
            findings=findings,
        )

    @abstractmethod
    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        """Perform static analysis inspection and return findings."""
        pass
