"""Abstract base class and interfaces for language parsers."""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Tuple, TypeVar
from app.models.schemas import (
    AnalysisIssue,
    ParserCapabilities,
    StructuralMetrics,
    SupportedLanguage,
)

T_AST = TypeVar("T_AST")


class BaseLanguageParser(ABC, Generic[T_AST]):
    """Abstract interface that all language parser adapters must implement.

    Guarantees a unified contract for syntax validation, AST parsing,
    diagnostics extraction, and structural metrics calculation across all
    supported languages.
    """

    @property
    @abstractmethod
    def language(self) -> SupportedLanguage:
        """Target programming language supported by this parser."""
        pass

    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Name of the parser engine (e.g. 'Python Built-in AST', 'Tree-sitter JavaScript')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if parser engine dependencies are installed and available."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ParserCapabilities:
        """Return capabilities manifest supported by this parser."""
        pass

    @abstractmethod
    def parse(self, code: str) -> Tuple[Optional[T_AST], List[AnalysisIssue]]:
        """Parse source code string into an AST / CST representation.

        Args:
            code: Source code text.

        Returns:
            Tuple of (AST object if parsed successfully or None, list of syntax/parser issues).
        """
        pass

    @abstractmethod
    def collect_metrics(self, code: str, ast: Optional[T_AST]) -> StructuralMetrics:
        """Calculate structural AST metrics from parsed representation.

        Args:
            code: Original source code text.
            ast: Parsed AST representation (if valid).

        Returns:
            StructuralMetrics object with counts of AST nodes, functions, classes, etc.
        """
        pass
