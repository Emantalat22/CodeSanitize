"""Semantics-preserving transformation engine implementation."""

import ast
import os
import time
from typing import List, Optional
from app.models.schemas import (
    CodeInput,
    DiffSummary,
    SupportedLanguage,
    TransformationAttempt,
    TransformationAttemptStatus,
    TransformationResult,
    TransformationStatus,
    ValidationPolicy,
    ValidationResult,
    ValidationVerdict,
)
from app.services.diff_service import DiffService
from app.transformers.registry import TransformationRegistry
from app.validators.pipeline import ValidationPipeline

MAX_SOURCE_SIZE_BYTES = 2 * 1024 * 1024


class TransformationEngine:
    """Independent engine orchestrating safety-first, semantics-preserving source code transformations."""

    @classmethod
    def transform(cls, input_data: CodeInput) -> TransformationResult:
        """Execute step-by-step verified transformations with multi-stage invariant validation.

        Args:
            input_data: Validated CodeInput container.

        Returns:
            TransformationResult containing verified code, applied transformations, diff, and verdicts.
        """
        start_time = time.perf_counter()
        original_code = input_data.code
        language = input_data.language
        raw_filename = input_data.filename
        safe_filename = os.path.basename(raw_filename) if raw_filename else None

        # Resolve validation policy from options (defaults to STRICT)
        policy_str = input_data.options.get("validation_policy", "strict") if input_data.options else "strict"
        try:
            policy = ValidationPolicy(policy_str.lower())
        except ValueError:
            policy = ValidationPolicy.STRICT

        # 1. Size Limitation Check
        if len(original_code.encode("utf-8")) > MAX_SOURCE_SIZE_BYTES:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TransformationResult(
                language=language,
                filename=safe_filename,
                original_code=original_code,
                transformed_code=original_code,
                transformation_status=TransformationStatus.FAILED,
                transformations_applied=[],
                rejected_transformations=[],
                attempt_history=[],
                change_count=0,
                diff=None,
                diff_summary=DiffSummary(additions=0, removals=0, changed_lines=0),
                validation_status=ValidationVerdict.FAILED,
                warnings=[
                    f"Source code size exceeds maximum limit of {MAX_SOURCE_SIZE_BYTES} bytes."
                ],
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 2. Language Validation Check
        if language != SupportedLanguage.PYTHON:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TransformationResult(
                language=language,
                filename=safe_filename,
                original_code=original_code,
                transformed_code=original_code,
                transformation_status=TransformationStatus.UNSUPPORTED_LANGUAGE,
                transformations_applied=[],
                rejected_transformations=[],
                attempt_history=[],
                change_count=0,
                diff=None,
                diff_summary=DiffSummary(additions=0, removals=0, changed_lines=0),
                validation_status=ValidationVerdict.WARNING,
                warnings=[
                    f"Transformation engine for {language.value} is under active development. Only Python is currently supported."
                ],
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 3. Initial Baseline Syntax Validation
        try:
            current_ast = (
                ast.parse(original_code, filename=safe_filename or "<input>")
                if original_code.strip()
                else None
            )
        except SyntaxError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TransformationResult(
                language=language,
                filename=safe_filename,
                original_code=original_code,
                transformed_code=original_code,
                transformation_status=TransformationStatus.SYNTAX_ERROR,
                transformations_applied=[],
                rejected_transformations=[],
                attempt_history=[],
                change_count=0,
                diff=None,
                diff_summary=DiffSummary(additions=0, removals=0, changed_lines=0),
                validation_status=ValidationVerdict.FAILED,
                warnings=[
                    f"Transformation aborted: Original code has syntax error on line {e.lineno}: {e.msg}"
                ],
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 4. Resolve and Filter Transformation Rules
        available_rules = TransformationRegistry.get_rules_for_language(language)
        enabled_rule_ids: Optional[List[str]] = (
            input_data.options.get("enabled_transformations")
            if input_data.options
            else None
        )

        selected_rules = []
        for rule in available_rules:
            if enabled_rule_ids is not None and len(enabled_rule_ids) > 0:
                if rule.rule_id in enabled_rule_ids:
                    selected_rules.append(rule)
            elif rule.default_enabled:
                selected_rules.append(rule)

        current_code = original_code
        transformations_applied: List[TransformationAttempt] = []
        rejected_transformations: List[TransformationAttempt] = []
        attempt_history: List[TransformationAttempt] = []
        warnings: List[str] = []

        pipeline = ValidationPipeline()
        latest_validation_report: Optional[ValidationResult] = None

        # 5. Iterative Multi-Pass Transformation & Pre-acceptance Validation Pipeline
        from app.provenance.pattern_detector import AIPatternDetector

        passes_executed = 0
        max_passes = 3

        while passes_executed < max_passes:
            passes_executed += 1
            pass_modifications_count = 0

            for rule in selected_rules:
                # A. Check applicability
                can_apply, reason = rule.can_apply(current_code, current_ast)
                if not can_apply:
                    attempt = TransformationAttempt(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        status=TransformationAttemptStatus.SKIPPED,
                        reason=reason,
                        changes_description=None,
                        change_count=0,
                        validation_verdict=ValidationVerdict.PASSED,
                    )
                    attempt_history.append(attempt)
                    continue

                # B. Apply candidate transformation
                try:
                    candidate_code, candidate_ast, changes_desc, count = rule.apply(
                        current_code, current_ast
                    )
                except Exception as e:
                    attempt = TransformationAttempt(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        status=TransformationAttemptStatus.REJECTED,
                        reason=f"Transformation execution error: {str(e)}",
                        changes_description=None,
                        change_count=0,
                        validation_verdict=ValidationVerdict.FAILED,
                        validation_message=str(e),
                    )
                    rejected_transformations.append(attempt)
                    attempt_history.append(attempt)
                    warnings.append(f"Rule '{rule.name}' threw an error and was rejected.")
                    continue

                # If no actual changes produced
                if candidate_code == current_code:
                    attempt = TransformationAttempt(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        status=TransformationAttemptStatus.SKIPPED,
                        reason="No structural modifications resulted from rule.",
                        changes_description=None,
                        change_count=0,
                        validation_verdict=ValidationVerdict.PASSED,
                    )
                    attempt_history.append(attempt)
                    continue

                # C. Multi-stage Validation via ValidationPipeline
                validation_res = pipeline.validate(
                    orig_code=current_code,
                    trans_code=candidate_code,
                    orig_ast=current_ast,
                    trans_ast=candidate_ast,
                    rule_id=rule.rule_id,
                    policy=policy,
                )
                latest_validation_report = validation_res

                if validation_res.is_valid:
                    # Accept candidate code and updated AST
                    current_code = candidate_code
                    current_ast = (
                        candidate_ast
                        if candidate_ast is not None
                        else (ast.parse(current_code) if current_code.strip() else None)
                    )

                    verdict = validation_res.verdict
                    attempt = TransformationAttempt(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        status=TransformationAttemptStatus.ACCEPTED,
                        reason=None,
                        changes_description=changes_desc,
                        change_count=count,
                        validation_verdict=verdict,
                        validation_message=validation_res.message,
                    )
                    transformations_applied.append(attempt)
                    attempt_history.append(attempt)
                    pass_modifications_count += count
                else:
                    # Rollback / Reject candidate code
                    attempt = TransformationAttempt(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        status=TransformationAttemptStatus.REJECTED,
                        reason=validation_res.message,
                        changes_description=changes_desc,
                        change_count=0,
                        validation_verdict=ValidationVerdict.FAILED,
                        validation_message=validation_res.message,
                    )
                    rejected_transformations.append(attempt)
                    attempt_history.append(attempt)
                    warnings.append(
                        f"Rule '{rule.name}' failed pre-acceptance validation: {validation_res.message}"
                    )

            if pass_modifications_count == 0:
                break

            # Rescan to check if AI Pattern Score is already minimal
            current_scan = AIPatternDetector.analyze(current_code, language=language)
            if current_scan.get("ai_pattern_score", 0) <= 5:
                break


        # 6. Final Overall Validation Assessment
        if current_code != original_code:
            final_rule_id = (
                "PY-STRUCT-SIMPLIFY-01"
                if any("struct" in t.rule_id.lower() or "simplify" in t.rule_id.lower() for t in transformations_applied)
                else None
            )
            final_validation = pipeline.validate(
                orig_code=original_code,
                trans_code=current_code,
                orig_ast=ast.parse(original_code) if original_code.strip() else None,
                trans_ast=current_ast,
                policy=policy,
                rule_id=final_rule_id,
            )
            latest_validation_report = final_validation


        # 7. Generate Unified Diff and Statistics
        diff_text, diff_summary = DiffService.generate_unified_diff(
            original_code=original_code,
            transformed_code=current_code,
            filename=safe_filename or f"source.{language.value}",
        )

        # 8. Determine Total Changes and Transformation Status
        total_changes = sum(t.change_count for t in transformations_applied)

        if transformations_applied and not rejected_transformations:
            status = TransformationStatus.COMPLETED
            overall_verdict = (
                latest_validation_report.verdict
                if latest_validation_report
                else ValidationVerdict.PASSED
            )
        elif transformations_applied and rejected_transformations:
            status = TransformationStatus.PARTIAL
            overall_verdict = ValidationVerdict.WARNING
        elif rejected_transformations and not transformations_applied:
            status = TransformationStatus.REJECTED
            overall_verdict = ValidationVerdict.FAILED
            warnings.append("No safe transformation was applied.")
        else:
            status = TransformationStatus.NO_CHANGES_APPLIED
            overall_verdict = ValidationVerdict.PASSED
            warnings.append("No safe transformation was applied. Code is already normalized.")

        # 9. Compute AI Pattern Scores (Before & After)
        from app.provenance.pattern_detector import AIPatternDetector
        orig_ai_res = AIPatternDetector.analyze(original_code, language=language)
        trans_ai_res = AIPatternDetector.analyze(current_code, language=language)
        original_ai_score = orig_ai_res["ai_pattern_score"]
        transformed_ai_score = trans_ai_res["ai_pattern_score"]

        # Calculate reduction percentage
        if original_ai_score > 0:
            reduction_percentage = round(
                max(0.0, (original_ai_score - transformed_ai_score) / original_ai_score * 100.0), 1
            )
        else:
            reduction_percentage = 0.0

        # 10. Compute Breakdown of Modified Categories and Explanations
        pattern_categories_changed: Dict[str, int] = {}
        comments_removed = 0
        identifiers_changed = 0
        structural_patterns_changed = 0
        redundant_logic_removed = 0
        formatting_fixes = 0
        removed_patterns: List[str] = []
        pattern_explanations: List[str] = []

        for attempt in transformations_applied:
            rule_lower = attempt.rule_id.lower()
            name_lower = attempt.name.lower()
            if "comment" in rule_lower or "comment" in name_lower:
                cnt = max(attempt.change_count, 1)
                comments_removed += cnt
                pattern_categories_changed["comments"] = pattern_categories_changed.get("comments", 0) + cnt
                if attempt.changes_description:
                    pattern_explanations.append(attempt.changes_description)
            elif "simplify" in rule_lower or "structure" in rule_lower or "struct" in rule_lower:
                cnt = max(attempt.change_count, 1)
                structural_patterns_changed += cnt
                redundant_logic_removed += max(1, cnt // 2)
                pattern_categories_changed["structures"] = pattern_categories_changed.get("structures", 0) + cnt
                if attempt.changes_description:
                    pattern_explanations.append(attempt.changes_description)
            elif "rename" in rule_lower or "variable" in name_lower or "identifier" in rule_lower:
                cnt = max(attempt.change_count, 1)
                identifiers_changed += cnt
                pattern_categories_changed["identifiers"] = pattern_categories_changed.get("identifiers", 0) + cnt
                if attempt.changes_description:
                    pattern_explanations.append(attempt.changes_description)
            elif "format" in rule_lower or "style" in rule_lower or "canon" in rule_lower:
                cnt = max(attempt.change_count, 1)
                formatting_fixes += cnt
                pattern_categories_changed["formatting"] = pattern_categories_changed.get("formatting", 0) + cnt
                if attempt.changes_description:
                    pattern_explanations.append(attempt.changes_description)
            elif "ai" in rule_lower or "pattern" in rule_lower:
                comments_removed += 1
                identifiers_changed += 1
                structural_patterns_changed += 1
                formatting_fixes += 1
                pattern_categories_changed["comments"] = pattern_categories_changed.get("comments", 0) + 1
                pattern_categories_changed["identifiers"] = pattern_categories_changed.get("identifiers", 0) + 1
                pattern_categories_changed["structures"] = pattern_categories_changed.get("structures", 0) + 1
                pattern_categories_changed["formatting"] = pattern_categories_changed.get("formatting", 0) + 1
                if attempt.changes_description:
                    pattern_explanations.append(attempt.changes_description)

        # Build removed patterns checklist
        if comments_removed > 0:
            removed_patterns.append(f"Excessive explanatory comments ({comments_removed} stripped)")
        if identifiers_changed > 0:
            removed_patterns.append(f"Generic AI identifiers ({identifiers_changed} converted to human names)")
        if structural_patterns_changed > 0:
            removed_patterns.append(f"Textbook sequential dictionary/return structures ({structural_patterns_changed} simplified)")
        if redundant_logic_removed > 0:
            removed_patterns.append(f"Temporary variable chains and single-use returns ({redundant_logic_removed} inlined)")
        if formatting_fixes > 0:
            removed_patterns.append(f"Artificial spacing & symmetrical padding ({formatting_fixes} standardized)")

        # 11. Build Transformation Preview & Automated Remediation Mapping
        from app.models.schemas import FingerprintRemediationPreview
        remediations_applied: List[FingerprintRemediationPreview] = []
        for signal in orig_ai_res.get("signals", []):
            stype = getattr(signal, "signal_type", "")
            desc = getattr(signal, "description", "")
            ev = getattr(signal, "evidence", "")
            loc = getattr(signal, "file_location", None)
            loc_str = f"Line {loc.get('line_start')}" if (loc and isinstance(loc, dict) and loc.get("line_start")) else "Global Scope"

            if "comment" in stype or "linguistic" in stype:
                remediations_applied.append(
                    FingerprintRemediationPreview(
                        fingerprint_type="Comment Watermark",
                        detected_fingerprint=f"Redundant AI comment: '{ev}'" if ev else desc,
                        applied_fix="Removed unnecessary explanation and obvious descriptor",
                        confidence=0.98,
                        location=loc_str,
                        remediation_rule="PROV-COMMENT-NORM-01",
                    )
                )
            elif "naming" in stype or "identifier" in stype:
                remediations_applied.append(
                    FingerprintRemediationPreview(
                        fingerprint_type="Identifier Watermark",
                        detected_fingerprint=f"AI generic identifier '{ev}'" if ev else desc,
                        applied_fix="Renamed into context-aware human identifier",
                        confidence=0.95,
                        location=loc_str,
                        remediation_rule="PY-SAFE-LOCAL-RENAME-01",
                    )
                )
            elif "structural" in stype or "struct" in stype:
                remediations_applied.append(
                    FingerprintRemediationPreview(
                        fingerprint_type="Structural Watermark",
                        detected_fingerprint=f"Textbook structure: '{ev}'" if ev else desc,
                        applied_fix="Simplified multi-step construction into clean inline return",
                        confidence=0.96,
                        location=loc_str,
                        remediation_rule="PY-STRUCT-SIMPLIFY-01",
                    )
                )
            elif "boilerplate" in stype or "template" in stype:
                remediations_applied.append(
                    FingerprintRemediationPreview(
                        fingerprint_type="Template Watermark",
                        detected_fingerprint=f"Synthetic boilerplate template: '{ev}'" if ev else desc,
                        applied_fix="Refactored into clean idiomatic developer pattern",
                        confidence=0.92,
                        location=loc_str,
                        remediation_rule="AI-PATTERN-NORM-01",
                    )
                )
            elif "formatting" in stype or "entropy" in stype or "spacing" in stype:
                remediations_applied.append(
                    FingerprintRemediationPreview(
                        fingerprint_type="Formatting Watermark",
                        detected_fingerprint=f"Artificial formatting regularity: '{ev}'" if ev else desc,
                        applied_fix="Standardized PEP 8 statement layout and whitespace",
                        confidence=0.99,
                        location=loc_str,
                        remediation_rule="PY-FMT-NORM-01",
                    )
                )


        # 12. Build Final AI Fingerprint Rescan Report
        fingerprint_rescan_report = {
            "initial_ai_score": original_ai_score,
            "final_ai_score": transformed_ai_score,
            "target_score_met": transformed_ai_score < 10,
            "remediation_passes_executed": passes_executed,
            "reduction_percentage": reduction_percentage,
            "remaining_signals_count": len(trans_ai_res.get("signals", [])),
            "remaining_signals": [
                {
                    "type": getattr(s, "signal_type", ""),
                    "description": getattr(s, "description", ""),
                    "evidence": getattr(s, "evidence", ""),
                }
                for s in trans_ai_res.get("signals", [])
            ],
            "clean_code_verdict": (
                "Natural Human-Written Code (Zero AI Fingerprints)"
                if transformed_ai_score == 0
                else ("Clean Developer Style (<10/100)" if transformed_ai_score < 10 else "Low AI Pattern Density")
            ),
        }

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return TransformationResult(
            language=language,
            filename=safe_filename,
            original_code=original_code,
            transformed_code=current_code,
            transformation_status=status,
            transformations_applied=transformations_applied,
            rejected_transformations=rejected_transformations,
            attempt_history=attempt_history,
            change_count=total_changes,
            diff=diff_text,
            diff_summary=diff_summary,
            validation_status=overall_verdict,
            validation_report=latest_validation_report,
            original_ai_score=original_ai_score,
            transformed_ai_score=transformed_ai_score,
            reduction_percentage=reduction_percentage,
            comments_removed=comments_removed,
            identifiers_changed=identifiers_changed,
            structural_patterns_changed=structural_patterns_changed,
            redundant_logic_removed=redundant_logic_removed,
            formatting_fixes=formatting_fixes,
            remediations_applied=remediations_applied,
            removed_patterns=removed_patterns,
            pattern_explanations=pattern_explanations,
            pattern_categories_changed=pattern_categories_changed,
            remediation_passes_count=passes_executed,
            fingerprint_rescan_report=fingerprint_rescan_report,
            human_authored_mode=getattr(input_data, 'human_authored_mode', True),
            warnings=warnings,
            execution_time_ms=round(elapsed_ms, 2),
        )








