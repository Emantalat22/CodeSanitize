"""Transformation rules registry and discovery."""

from typing import Dict, List, Optional
from app.models.schemas import SupportedLanguage, TransformationRuleSpec
from app.transformers.base import BaseTransformationRule
from app.transformers.python.ai_pattern_norm import AIPatternNormalizationRule
from app.transformers.python.ast_canonical import AstCanonicalFormatRule
from app.transformers.python.code_simplification import PythonCodeSimplificationRule
from app.transformers.python.comment_norm import ProvCommentNormRule
from app.transformers.python.formatting_norm import FormattingNormalizationRule
from app.transformers.python.local_variable_rename import SafeLocalVariableRenameRule
from app.transformers.python.style_norm import ProvStyleNormRule


class TransformationRegistry:
    """Registry maintaining available semantics-preserving transformation rules."""

    _rules: Dict[str, BaseTransformationRule] = {}

    @classmethod
    def initialize(cls):
        """Register default safe transformation rules in prioritized pipeline order."""
        cls._rules.clear()
        # 1. Normalize and strip redundant AI-generated comments
        cls.register(ProvCommentNormRule())
        # 2. Structural & dictionary construction simplification
        cls.register(PythonCodeSimplificationRule())
        # 3. Safely normalize generic local variables to human-like descriptive identifiers
        cls.register(SafeLocalVariableRenameRule())
        # 4. Normalize whitespace and collapse excessive blank lines
        cls.register(ProvStyleNormRule())
        # 5. Standard formatting normalization
        cls.register(FormattingNormalizationRule())
        # 6. AST canonical form
        cls.register(AstCanonicalFormatRule())
        # 7. Comprehensive AI pattern normalization composite
        cls.register(AIPatternNormalizationRule())

    @classmethod
    def register(cls, rule: BaseTransformationRule):
        """Register a transformation rule."""
        cls._rules[rule.rule_id] = rule

    @classmethod
    def get_rule(cls, rule_id: str) -> Optional[BaseTransformationRule]:
        """Retrieve rule by ID."""
        if not cls._rules:
            cls.initialize()
        return cls._rules.get(rule_id)

    @classmethod
    def get_rules_for_language(
        cls, language: SupportedLanguage
    ) -> List[BaseTransformationRule]:
        """Retrieve all rules applicable to a specific programming language."""
        if not cls._rules:
            cls.initialize()
        return [
            rule
            for rule in cls._rules.values()
            if language in rule.supported_languages
        ]

    @classmethod
    def list_rule_specs(
        cls, language: Optional[SupportedLanguage] = None
    ) -> List[TransformationRuleSpec]:
        """List rule specifications."""
        if not cls._rules:
            cls.initialize()
        if language is not None:
            return [
                rule.get_spec()
                for rule in cls._rules.values()
                if language in rule.supported_languages
            ]
        return [rule.get_spec() for rule in cls._rules.values()]


# Initialize registry on import
TransformationRegistry.initialize()
