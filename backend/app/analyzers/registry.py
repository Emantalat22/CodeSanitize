"""Registry for registering and discovering modular static analyzer engines."""

import ast
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.analyzers.code_metrics import CodeMetricsAnalyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.fingerprint_analyzer import FingerprintAnalyzer
from app.analyzers.quality_analyzer import CodeQualityAnalyzer
from app.analyzers.security import SecurityAnalyzer
from app.analyzers.similarity_engine import SimilarityAnalyzer
from app.models.schemas import (
    AnalyzerReport,
    CodeMetrics,
    SupportedLanguage,
)


class AnalyzerRegistry:
    """Manages available static code intelligence analyzers and runs analysis pipelines."""

    _analyzers: Dict[str, BaseAnalyzer] = {}

    @classmethod
    def register(cls, analyzer: BaseAnalyzer) -> None:
        """Register an analyzer module."""
        cls._analyzers[analyzer.analyzer_id] = analyzer

    @classmethod
    def get_analyzer(cls, analyzer_id: str) -> Optional[BaseAnalyzer]:
        """Get an analyzer by ID."""
        return cls._analyzers.get(analyzer_id)

    @classmethod
    def list_analyzers(
        cls, language: Optional[SupportedLanguage] = None
    ) -> List[BaseAnalyzer]:
        """List all analyzers, optionally filtered by supported language."""
        if language is None:
            return list(cls._analyzers.values())
        return [
            a for a in cls._analyzers.values() if language in a.supported_languages
        ]

    @classmethod
    def run_all(
        cls,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: CodeMetrics,
        language: SupportedLanguage = SupportedLanguage.PYTHON,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[AnalyzerReport]:
        """Execute all compatible analyzers and collect reports."""
        options = options or {}
        reports: List[AnalyzerReport] = []
        applicable = cls.list_analyzers(language)

        for analyzer in applicable:
            report = analyzer.run(code, ast_tree, metrics, options)
            reports.append(report)

        return reports


# Register default analyzers
AnalyzerRegistry.register(CodeMetricsAnalyzer())
AnalyzerRegistry.register(ComplexityAnalyzer())
AnalyzerRegistry.register(SecurityAnalyzer())
AnalyzerRegistry.register(CodeQualityAnalyzer())
AnalyzerRegistry.register(FingerprintAnalyzer())
AnalyzerRegistry.register(SimilarityAnalyzer())
