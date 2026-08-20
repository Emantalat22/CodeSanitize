"""Modular static code analyzers for CodeSanitize."""

from app.analyzers.base import BaseAnalyzer
from app.analyzers.code_metrics import CodeMetricsAnalyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.fingerprint_analyzer import FingerprintAnalyzer
from app.analyzers.nonfunctional import NonFunctionalAnalyzer
from app.analyzers.quality_analyzer import CodeQualityAnalyzer
from app.analyzers.registry import AnalyzerRegistry
from app.analyzers.security import SecurityAnalyzer
from app.analyzers.similarity_engine import SimilarityAnalyzer

# Alias for backwards compatibility
SecurityPatternAnalyzer = SecurityAnalyzer

__all__ = [
    "AnalyzerRegistry",
    "BaseAnalyzer",
    "CodeMetricsAnalyzer",
    "CodeQualityAnalyzer",
    "ComplexityAnalyzer",
    "FingerprintAnalyzer",
    "NonFunctionalAnalyzer",
    "SecurityAnalyzer",
    "SecurityPatternAnalyzer",
    "SimilarityAnalyzer",
]
