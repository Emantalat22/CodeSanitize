"""Abstract base class and interfaces for modular validation pipeline stages."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.models.schemas import SupportedLanguage, ValidationCheckResult, ValidationResult


class BaseValidatorStage(ABC):
    """Abstract interface for an independent validation stage in the validation pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this validation stage."""
        pass

    @property
    def language(self) -> SupportedLanguage:
        """Target programming language."""
        return SupportedLanguage.PYTHON

    @abstractmethod
    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST],
        trans_ast: Optional[ast.AST],
        rule_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationCheckResult:
        """Execute validation check comparing original baseline against candidate transformed code.

        Args:
            orig_code: Original source code before transformation.
            trans_code: Transformed candidate source code.
            orig_ast: Baseline AST of original code (if available).
            trans_ast: Candidate AST of transformed code (if available).
            rule_id: Identifier of the transformation rule applied.
            options: Additional validator configuration options.

        Returns:
            ValidationCheckResult containing pass status, severity, and diagnostic details.
        """
        pass


class BaseValidator(ABC):
    """Abstract interface for overall validation coordinator (backward compatibility)."""

    @property
    @abstractmethod
    def language(self) -> SupportedLanguage:
        """Target programming language."""
        pass

    @abstractmethod
    def validate(
        self,
        original_code: str,
        transformed_code: str,
        original_ast: Optional[Any] = None,
        rule_id: Optional[str] = None,
    ) -> ValidationResult:
        """Perform validation and return ValidationResult."""
        pass
