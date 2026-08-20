"""Coordinated multi-stage pre-acceptance validation pipeline."""

import ast
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.schemas import (
    SupportedLanguage,
    ValidationCheckResult,
    ValidationConfidenceLevel,
    ValidationDiagnostic,
    ValidationPolicy,
    ValidationResult,
    ValidationRiskFlag,
    ValidationTestCase,
    ValidationVerdict,
)
from app.validators.behavioral_framework import StaticBehaviorValidator
from app.validators.control_flow_validator import ControlFlowValidator
from app.validators.data_flow_validator import DataFlowValidator
from app.validators.import_validator import ImportValidator
from app.validators.interface_validator import PublicInterfaceValidator
from app.validators.reflection_validator import ReflectionSafeguardValidator
from app.validators.side_effect_validator import SideEffectValidator
from app.validators.structural_validator import AstStructuralValidator
from app.validators.syntax_validator import SyntaxValidator


class ValidationPipeline:
    """Orchestrates independent validation stages with policy enforcement and structured diagnostics."""

    def __init__(self):
        self.syntax_validator = SyntaxValidator()
        self.structural_validator = AstStructuralValidator()
        self.interface_validator = PublicInterfaceValidator()
        self.control_flow_validator = ControlFlowValidator()
        self.data_flow_validator = DataFlowValidator()
        self.import_validator = ImportValidator()
        self.reflection_validator = ReflectionSafeguardValidator()
        self.side_effect_validator = SideEffectValidator()
        self.behavior_validator = StaticBehaviorValidator()

    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST] = None,
        trans_ast: Optional[ast.AST] = None,
        rule_id: Optional[str] = None,
        policy: ValidationPolicy = ValidationPolicy.STRICT,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Run all validation stages sequentially and formulate comprehensive report.

        Args:
            orig_code: Original source text.
            trans_code: Candidate transformed source text.
            orig_ast: Pre-parsed baseline AST.
            trans_ast: Pre-parsed candidate AST.
            rule_id: Active transformation rule ID.
            policy: Enforcement policy (STRICT, BALANCED, PERMISSIVE).
            options: Additional validator configuration options.

        Returns:
            ValidationResult with verdict, confidence, risk flags, and check results.
        """
        options = options or {}
        validators_run: List[str] = []
        passed_checks: List[ValidationCheckResult] = []
        warnings: List[ValidationCheckResult] = []
        failures: List[ValidationCheckResult] = []
        risk_flags: List[ValidationRiskFlag] = []
        structural_changes: List[str] = []
        interface_changes: List[str] = []
        test_cases: List[ValidationTestCase] = []

        # Baseline AST parse
        try:
            baseline_ast = (
                orig_ast
                if orig_ast is not None
                else ast.parse(orig_code, filename="<original>")
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                verdict=ValidationVerdict.FAILED,
                confidence_level=ValidationConfidenceLevel.LOW,
                policy_applied=policy,
                syntax_valid=False,
                semantic_invariants_preserved=False,
                validators_run=["Baseline Parse"],
                passed_checks=[],
                warnings=[],
                failures=[
                    ValidationCheckResult(
                        check_name="Baseline Parse",
                        passed=False,
                        severity=ValidationVerdict.FAILED,
                        details=f"Original baseline code had syntax error on line {e.lineno}: {e.msg}",
                    )
                ],
                diagnostics=[
                    ValidationDiagnostic(
                        check_name="Baseline Parse",
                        passed=False,
                        details="Original baseline code was syntactically invalid.",
                    )
                ],
                structural_changes=[],
                interface_changes=[],
                risk_flags=[],
                test_cases=[],
                message="Validation rejected: Original source code was syntactically invalid.",
            )

        # Stage 1: Syntax Validator
        validators_run.append(self.syntax_validator.name)
        syntax_res = self.syntax_validator.validate(
            orig_code, trans_code, baseline_ast, trans_ast, rule_id, options
        )
        if syntax_res.severity == ValidationVerdict.FAILED:
            failures.append(syntax_res)
            return ValidationResult(
                is_valid=False,
                verdict=ValidationVerdict.FAILED,
                confidence_level=ValidationConfidenceLevel.LOW,
                policy_applied=policy,
                syntax_valid=False,
                semantic_invariants_preserved=False,
                validators_run=validators_run,
                passed_checks=[],
                warnings=[],
                failures=failures,
                diagnostics=[
                    ValidationDiagnostic(
                        check_name=syntax_res.check_name,
                        passed=False,
                        details=syntax_res.details,
                    )
                ],
                structural_changes=[],
                interface_changes=[],
                risk_flags=[],
                test_cases=[],
                message=f"Transformation rejected: {syntax_res.details}",
            )
        else:
            passed_checks.append(syntax_res)

        # Candidate AST parse
        try:
            candidate_ast = (
                trans_ast
                if trans_ast is not None
                else ast.parse(trans_code, filename="<transformed>")
            )
        except Exception:
            candidate_ast = None


        stages = [
            self.structural_validator,
            self.interface_validator,
            self.control_flow_validator,
            self.data_flow_validator,
            self.import_validator,
            self.reflection_validator,
            self.side_effect_validator,
            self.behavior_validator,
        ]

        for stage in stages:
            validators_run.append(stage.name)
            check_res = stage.validate(
                orig_code, trans_code, baseline_ast, candidate_ast, rule_id, options
            )

            # Collect risk flags
            if "risk_flags" in check_res.context:
                for rf in check_res.context["risk_flags"]:
                    try:
                        flag_enum = ValidationRiskFlag(rf)
                        if flag_enum not in risk_flags:
                            risk_flags.append(flag_enum)
                    except ValueError:
                        pass

            if check_res.severity == ValidationVerdict.FAILED:
                failures.append(check_res)
            elif check_res.severity == ValidationVerdict.WARNING:
                warnings.append(check_res)
            else:
                passed_checks.append(check_res)

        # Generate test cases if candidate_ast exists
        if candidate_ast:
            test_cases = self.behavior_validator.generate_test_cases(candidate_ast)

        # Build legacy diagnostics list
        legacy_diags: List[ValidationDiagnostic] = [
            ValidationDiagnostic(
                check_name=c.check_name, passed=c.passed, details=c.details
            )
            for c in passed_checks + warnings + failures
        ]

        # Policy Enforcement Logic
        # 1. Any concrete failure -> Always FAILED
        if failures:
            overall_verdict = ValidationVerdict.FAILED
            is_valid = False
            confidence = ValidationConfidenceLevel.LOW
            failure_msgs = [f.details for f in failures]
            summary_msg = f"Transformation rejected: Concrete validation check failed: {'; '.join(failure_msgs)}"

        # 2. Warnings present (no failures)
        elif warnings:
            warning_msgs = [w.details for w in warnings]
            if policy == ValidationPolicy.STRICT:
                overall_verdict = ValidationVerdict.FAILED
                is_valid = False
                confidence = ValidationConfidenceLevel.LOW
                summary_msg = (
                    f"Transformation rejected under STRICT policy due to warnings: {'; '.join(warning_msgs)}"
                )
            elif policy == ValidationPolicy.BALANCED:
                overall_verdict = ValidationVerdict.WARNING
                is_valid = True
                confidence = ValidationConfidenceLevel.MEDIUM
                summary_msg = (
                    f"Transformation passed with caveats (BALANCED policy): {'; '.join(warning_msgs)}"
                )
            else:  # PERMISSIVE
                overall_verdict = ValidationVerdict.WARNING
                is_valid = True
                confidence = ValidationConfidenceLevel.MEDIUM
                summary_msg = (
                    f"Transformation accepted under PERMISSIVE policy: {'; '.join(warning_msgs)}"
                )

        # 3. All checks passed cleanly
        else:
            overall_verdict = ValidationVerdict.PASSED
            is_valid = True
            confidence = ValidationConfidenceLevel.HIGH
            summary_msg = "All pre-acceptance syntax, signature, structural, control-flow, and data-flow invariants strictly passed."

        return ValidationResult(
            is_valid=is_valid,
            verdict=overall_verdict,
            confidence_level=confidence,
            policy_applied=policy,
            syntax_valid=True,
            semantic_invariants_preserved=len(failures) == 0,
            validators_run=validators_run,
            passed_checks=passed_checks,
            warnings=warnings,
            failures=failures,
            diagnostics=legacy_diags,
            structural_changes=structural_changes,
            interface_changes=interface_changes,
            risk_flags=risk_flags,
            test_cases=test_cases,
            message=summary_msg,
            timestamp=datetime.now(timezone.utc),
        )
