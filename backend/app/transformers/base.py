"""Abstract base class and interfaces for deterministic semantics-preserving transformations."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from app.models.schemas import (
    SupportedLanguage,
    TransformationRuleSpec,
    TransformationSafetyLevel,
)


class BaseTransformationRule(ABC):
    """Abstract interface for a deterministic, semantics-preserving transformation rule.

    Every transformation rule must be self-contained, declare what it modifies,
    state its safety classification, and provide a pre-check to confirm applicability.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this transformation rule (e.g. 'PY-FMT-NORM-01')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the transformation rule."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Clear description of what the transformation modifies."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[SupportedLanguage]:
        """List of languages compatible with this rule."""
        pass

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        """Safety rating of the rule."""
        return TransformationSafetyLevel.SAFE_CONSERVATIVE

    @property
    def default_enabled(self) -> bool:
        """Whether this rule is enabled by default."""
        return True

    def get_spec(self) -> TransformationRuleSpec:
        """Return the rule specification metadata."""
        return TransformationRuleSpec(
            rule_id=self.rule_id,
            name=self.name,
            description=self.description,
            supported_languages=self.supported_languages,
            safety_level=self.safety_level,
            default_enabled=self.default_enabled,
        )

    @abstractmethod
    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        """Determine whether this transformation can be safely applied to the source.

        Args:
            code: Current source code string.
            ast_tree: Parsed AST representation (if available).

        Returns:
            Tuple of (can_apply: bool, reason: str).
        """
        pass

    @abstractmethod
    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        """Apply the semantics-preserving transformation to the source/AST.

        Args:
            code: Current source code string.
            ast_tree: Parsed AST representation.

        Returns:
            Tuple of:
            - new_code: Resulting transformed source code string.
            - new_ast: Updated AST (or None if string-level formatting).
            - changes_description: Explanation of specific edits performed.
            - change_count: Count of individual modifications applied.
        """
        pass
