"""AI Code Provenance Analysis Orchestrator."""

import time
from typing import List
from app.models.schemas import CodeInput, SupportedLanguage
from app.parsers.language_detector import LanguageDetector
from app.provenance.comment_analyzer import CommentPatternAnalyzer
from app.provenance.identifier_analyzer import IdentifierPatternAnalyzer
from app.provenance.models import ProvenanceReport, ProvenanceSignal
from app.provenance.pattern_detector import AIPatternDetector
from app.provenance.style_analyzer import StylePatternAnalyzer


class ProvenanceService:
    """Orchestrates deterministic static inspection of AI-style and generated code patterns."""

    @classmethod
    def analyze_provenance(cls, input_data: CodeInput) -> ProvenanceReport:
        """Run full provenance static analysis suite."""
        start_time = time.perf_counter()
        code = input_data.code or ""
        lang = input_data.language

        if not lang or lang == SupportedLanguage.AUTO or str(lang).lower() == "auto":
            lang = LanguageDetector.detect(code, input_data.filename)
        elif isinstance(lang, str):
            try:
                lang = SupportedLanguage(lang.lower())
            except Exception:
                lang = SupportedLanguage.PYTHON

        if not code.strip():
            return ProvenanceReport(
                provenance_score=0,
                ai_pattern_score=0,
                confidence_level="high",
                confidence_score=0.95,
                risk_level="low",
                signals_detected=[],
                detected_patterns=[],
                ai_pattern_breakdown={},
                recommendations=["Empty source code provided; no synthetic traits found."],
                execution_time_ms=0.0,
            )

        # 1. Run Modular Analyzers
        comment_res = CommentPatternAnalyzer.analyze(code, language=lang)
        identifier_res = IdentifierPatternAnalyzer.analyze(code, language=lang)
        style_res = StylePatternAnalyzer.analyze(code, language=lang)
        pattern_res = AIPatternDetector.analyze(code, language=lang)

        # 2. Aggregate Signals
        all_signals: List[ProvenanceSignal] = []
        all_signals.extend(comment_res.obvious_comments)
        all_signals.extend(identifier_res.generic_identifiers)
        all_signals.extend(style_res.signals)
        for sig in pattern_res["signals"]:
            # avoid duplicates by evidence and description
            if not any(s.evidence == sig.evidence and s.description == sig.description for s in all_signals):
                all_signals.append(sig)

        # 3. Calculate Deterministic Provenance Score (0 - 100)
        comment_pts = min(comment_res.redundant_comments_count * 12, 40)
        identifier_pts = min(identifier_res.generic_identifiers_count * 8, 30)
        style_pts = min(len(style_res.signals) * 10, 30)

        raw_score = comment_pts + identifier_pts + style_pts
        final_score = min(max(raw_score, 0), 100)

        ai_pattern_score = max(final_score, pattern_res["ai_pattern_score"])

        # 4. Determine Confidence Level
        if len(code.splitlines()) < 8:
            confidence = "low"
        elif len(all_signals) >= 3:
            confidence = "high"
        else:
            confidence = "medium"

        # 5. Generate Actionable Provenance & Normalization Recommendations
        recommendations: List[str] = []
        if comment_res.redundant_comments_count > 0:
            recommendations.append(
                f"Remove {comment_res.redundant_comments_count} redundant/explanatory comments that state obvious code operations (or enable PROV-COMMENT-NORM-01)."
            )
        if identifier_res.generic_identifiers_count > 0:
            recommendations.append(
                f"Rename {identifier_res.generic_identifiers_count} generic variable names (e.g. temp_value, result_data) with domain-specific descriptive identifiers."
            )
        if style_res.excessive_regularity:
            recommendations.append(
                "Standardize and format code structure to match idiomatic project conventions using PROV-STYLE-NORM-01."
            )
        for rec in pattern_res.get("recommendations", []):
            if rec not in recommendations and "zero detectable" not in rec.lower():
                recommendations.append(rec)
        if not recommendations:
            recommendations.append("Code exhibits natural idiomatic structuring with zero obvious synthetic boilerplate.")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        risk_level = "high" if ai_pattern_score >= 60 else "medium" if ai_pattern_score >= 30 else "low"
        conf_score = pattern_res.get("confidence_score", 0.85)

        detected_patterns = [
            {
                "pattern_type": s.signal_type,
                "severity": s.severity,
                "confidence": s.confidence,
                "description": s.description,
                "evidence": s.evidence,
                "file_location": s.file_location,
            }
            for s in all_signals
        ]

        return ProvenanceReport(
            provenance_score=final_score,
            ai_pattern_score=ai_pattern_score,
            confidence_level=confidence,
            confidence_score=conf_score,
            risk_level=risk_level,
            signals_detected=all_signals,
            detected_patterns=detected_patterns,
            ai_pattern_breakdown=pattern_res.get("breakdown", {}),
            comment_analysis=comment_res,
            identifier_analysis=identifier_res,
            style_analysis=style_res,
            recommendations=recommendations,
            execution_time_ms=round(elapsed_ms, 2),
        )
