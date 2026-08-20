"""Python validator adapter wrapping ValidationPipeline."""

from typing import Any, Optional
from app.models.schemas import SupportedLanguage, ValidationPolicy, ValidationResult
from app.validators.base import BaseValidator
from app.validators.pipeline import ValidationPipeline


class PythonTransformationValidator(BaseValidator):
    """Multi-stage conservative transformation validator for Python code.

    Delegates to modular ValidationPipeline checking:
    - Syntax Integrity
    - AST Structural Invariants
    - Public Interface & Signatures
    - Control-Flow Invariants
    - Data-Flow & Scoping Safeguards
    - Imports & Dependencies Invariants
    - Reflection & Eval Safeguards
    - Side-Effect Sensitivity Analysis
    - Static Behavioral Equivalence
    """

    def __init__(self, policy: ValidationPolicy = ValidationPolicy.STRICT):
        self.pipeline = ValidationPipeline()
        self.policy = policy

    @property
    def language(self) -> SupportedLanguage:
        return SupportedLanguage.PYTHON

    def validate(
        self,
        original_code: str,
        transformed_code: str,
        original_ast: Optional[Any] = None,
        rule_id: Optional[str] = None,
        policy: Optional[ValidationPolicy] = None,
    ) -> ValidationResult:
        active_policy = policy or self.policy
        return self.pipeline.validate(
            orig_code=original_code,
            trans_code=transformed_code,
            orig_ast=original_ast,
            rule_id=rule_id,
            policy=active_policy,
        )
