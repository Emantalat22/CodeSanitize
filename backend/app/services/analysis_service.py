import ast
from datetime import datetime, timezone
import os
import time
from typing import List, Optional

from app.analyzers.code_metrics import CodeMetricsAnalyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.fingerprint_analyzer import FingerprintAnalyzer
from app.analyzers.nonfunctional import NonFunctionalAnalyzer
from app.analyzers.registry import AnalyzerRegistry
from app.analyzers.security import SecurityAnalyzer
from app.models.cir import IRProgram
from app.models.schemas import (
    AnalysisFinding,
    AnalysisIssue,
    AnalysisResult,
    AnalysisStatus,
    CodeInput,
    CodeMetrics,
    ComplexityFunction,
    ComplexityFunctionMetric,
    ComplexityMetrics,
    ComplexityReport,
    FindingCategory,
    IssueSeverity,
    NonFunctionalArtifact,
    ParserCapabilities,
    SecurityReport,
    StructuralFingerprint,
    SupportedLanguage,
)
from app.parsers.cir_extractor import CIRExtractor
from app.parsers.registry import ParserRegistry
from app.services.history_service import HistoryService
from app.services.quality_service import QualityService
from app.services.recommendation_service import RecommendationService


# Max input size constraint (2 MB)
MAX_SOURCE_SIZE_BYTES = 2 * 1024 * 1024


class AnalysisService:
    """Independent service orchestrating multi-language parsing, AST metrics collection, and artifact scanning."""

    @classmethod
    def analyze(cls, input_data: CodeInput) -> AnalysisResult:
        """Perform deterministic code analysis with Multi-Language Code Intelligence and Risk Assessment.

        Args:
            input_data: Validated CodeInput containing code, language, and optional metadata.

        Returns:
            Structured AnalysisResult with verified parser metrics, intelligence findings, and score.
        """
        start_time = time.perf_counter()
        code = input_data.code
        raw_filename = input_data.filename
        safe_filename = os.path.basename(raw_filename) if raw_filename else None

        # 1. Automatic Language Detection (if language is unspecified or auto)
        language = input_data.language
        if not language or language == "auto" or str(language).lower() == "auto":
            language = ParserRegistry.detect_language(code, raw_filename)

        code_bytes = code.encode("utf-8")
        code_length = len(code)
        line_count = len(code.splitlines()) if code else 0

        # 2. Security Check: Size Limitation
        if len(code_bytes) > MAX_SOURCE_SIZE_BYTES:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AnalysisResult(
                language=language,
                filename=safe_filename,
                quality_score=0,
                overall_score=0,
                code_length=code_length,
                line_count=line_count,
                syntax_valid=False,
                parser_used="Validation Guard",
                analysis_status=AnalysisStatus.FAILED,
                issues=[
                    AnalysisIssue(
                        rule_id="SEC-SIZE-EXCEEDED",
                        message=f"Source code size ({len(code_bytes)} bytes) exceeds maximum limit of {MAX_SOURCE_SIZE_BYTES} bytes.",
                        severity=IssueSeverity.ERROR,
                    )
                ],
                findings=[],
                metrics=CodeMetrics(lines_of_code=line_count, raw_character_count=code_length),
                structural_metrics=CodeMetrics(lines_of_code=line_count, raw_character_count=code_length),
                complexity_report=ComplexityReport(),
                complexity_metrics=ComplexityMetrics(),
                security_report=SecurityReport(risk_level="Critical"),
                detected_nonfunctional_artifacts=[],
                capabilities=ParserCapabilities(
                    ast_available=False,
                    syntax_validation=False,
                    metrics_collection=False,
                    non_functional_detection=False,
                    engine_name="Size Guard",
                ),
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 3. Select Language Parser
        parser = ParserRegistry.get_parser(language)

        if parser is None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AnalysisResult(
                language=language,
                filename=safe_filename,
                quality_score=50,
                overall_score=50,
                code_length=code_length,
                line_count=line_count,
                syntax_valid=False,
                parser_used="None",
                analysis_status=AnalysisStatus.UNSUPPORTED_LANGUAGE,
                issues=[
                    AnalysisIssue(
                        rule_id="LANG-UNSUPPORTED",
                        message=f"Programming language '{language.value}' is not supported yet.",
                        severity=IssueSeverity.WARNING,
                    )
                ],
                findings=[],
                metrics=CodeMetrics(lines_of_code=line_count, raw_character_count=code_length),
                structural_metrics=CodeMetrics(lines_of_code=line_count, raw_character_count=code_length),
                complexity_report=ComplexityReport(),
                complexity_metrics=ComplexityMetrics(),
                security_report=SecurityReport(risk_level="Low"),
                detected_nonfunctional_artifacts=NonFunctionalAnalyzer.analyze(code, language),
                capabilities=ParserCapabilities(
                    ast_available=False,
                    syntax_validation=False,
                    metrics_collection=False,
                    non_functional_detection=True,
                    engine_name="Unsupported Language",
                ),
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 4. Parse Source Code & Validate Syntax
        ast_tree, parser_issues = parser.parse(code)
        has_syntax_errors = any(
            issue.severity == IssueSeverity.ERROR for issue in parser_issues
        )
        syntax_valid = (not has_syntax_errors) and (
            ast_tree is not None or not code.strip()
        )

        analysis_status = (
            AnalysisStatus.COMPLETED
            if syntax_valid
            else AnalysisStatus.SYNTAX_ERROR
        )

        # 5. Extract Code Metrics & Complexity Report
        if language == SupportedLanguage.PYTHON and (isinstance(ast_tree, ast.AST) or not code.strip()):
            code_metrics = CodeMetricsAnalyzer.compute_metrics(code, ast_tree)
            complexity_report = ComplexityAnalyzer.compute_complexity(ast_tree)
            fingerprint = FingerprintAnalyzer.generate_fingerprint(ast_tree)

        else:
            # Multi-language AST & CIR extraction
            code_metrics = parser.collect_metrics(code, ast_tree)
            cir = CIRExtractor.extract(code, language, ast_tree)

            ranked_funcs: List[ComplexityFunction] = []
            func_metrics: List[ComplexityFunctionMetric] = []

            for fn in cir.functions:
                ranked_funcs.append(
                    ComplexityFunction(
                        name=fn.name,
                        complexity=fn.cyclomatic_complexity,
                        risk="low" if fn.cyclomatic_complexity <= 5 else "medium",
                        line_start=fn.line_start,
                        nesting_depth=fn.max_nesting_depth,
                        statement_count=fn.statement_count,
                    )
                )
                func_metrics.append(
                    ComplexityFunctionMetric(
                        name=fn.name,
                        line_start=fn.line_start,
                        cyclomatic_complexity=fn.cyclomatic_complexity,
                        nesting_depth=fn.max_nesting_depth,
                        statement_count=fn.statement_count,
                    )
                )

            max_c = max([f.complexity for f in ranked_funcs], default=code_metrics.cyclomatic_complexity)
            avg_c = round(sum([f.complexity for f in ranked_funcs]) / max(len(ranked_funcs), 1), 1) if ranked_funcs else float(max_c)

            complexity_report = ComplexityReport(
                cyclomatic_complexity=code_metrics.cyclomatic_complexity,
                branching_count=code_metrics.control_flow_node_count,
                loop_count=sum(1 for cf in cir.control_flows if cf.kind == "loop"),
                max_nesting_depth=cir.max_nesting_depth,
                exception_handling_count=sum(1 for cf in cir.control_flows if cf.kind == "try_catch"),
                maximum_complexity=max_c,
                average_complexity=avg_c,
                most_complex_functions=ranked_funcs,
                function_complexities=func_metrics,
                complexity_level="High" if max_c > 15 else "Medium" if max_c > 8 else "Low",
            )
            fingerprint = None

        complexity_metrics = ComplexityMetrics(
            cyclomatic_complexity=complexity_report.cyclomatic_complexity,
            branching_count=complexity_report.branching_count,
            loop_count=complexity_report.loop_count,
            max_nesting_depth=complexity_report.max_nesting_depth,
            exception_handling_count=complexity_report.exception_handling_count,
            function_complexities=complexity_report.function_complexities,
        )

        # 6. Analyze Non-functional Artifacts
        artifacts = NonFunctionalAnalyzer.analyze(
            code=code,
            language=language,
            comment_count=code_metrics.comment_count,
            docstring_count=code_metrics.docstring_count,
        )

        # 7. Execute Multi-Language Intelligence Analyzers Suite
        analyzer_reports = AnalyzerRegistry.run_all(
            code=code,
            ast_tree=ast_tree if language == SupportedLanguage.PYTHON else None,
            metrics=code_metrics,
            language=language,
            options=input_data.options,
        )

        # Aggregate Findings
        all_findings: List[AnalysisFinding] = []
        for r in analyzer_reports:
            all_findings.extend(r.findings)

        # 8. Generate Security Report
        security_report = SecurityAnalyzer.generate_report(all_findings)

        # 9. Collect Patterns, Risk Categories, and Generate Recommendations
        detected_patterns: List[str] = []
        risk_categories: List[str] = []

        for f in all_findings:
            if f.category == FindingCategory.SECURITY:
                if f.title not in risk_categories:
                    risk_categories.append(f.title)
            elif f.category == FindingCategory.COMPLEXITY:
                if f.title not in detected_patterns:
                    detected_patterns.append(f.title)

        recommendations = RecommendationService.generate_recommendations(
            findings=all_findings,
            complexity=complexity_report,
            metrics=code_metrics,
            security=security_report,
        )

        # 10. Calculate Deterministic Quality Score (0-100)
        if syntax_valid:
            quality_score = QualityService.calculate_quality_score(
                findings=all_findings,
                complexity=complexity_report,
                metrics=code_metrics,
            )
        else:
            quality_score = 0

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        now_utc = datetime.now(timezone.utc)

        result = AnalysisResult(
            language=language,
            filename=safe_filename,
            timestamp=now_utc,
            analysis_timestamp=now_utc,
            quality_score=quality_score,
            overall_score=quality_score,
            metrics=code_metrics,
            structural_metrics=code_metrics,
            complexity_report=complexity_report,
            complexity_metrics=complexity_metrics,
            security_report=security_report,
            findings=all_findings,
            recommendations=recommendations,
            code_length=code_length,
            line_count=line_count,
            syntax_valid=syntax_valid,
            parser_used=parser.parser_name,
            analysis_status=analysis_status,
            issues=parser_issues,
            detected_nonfunctional_artifacts=artifacts,
            fingerprint=fingerprint,
            analyzer_reports=analyzer_reports,
            detected_patterns=detected_patterns,
            risk_categories=risk_categories,
            capabilities=parser.get_capabilities(),
            execution_time_ms=round(elapsed_ms, 2),
        )

        # Save single-file scan to local history (if code is non-empty)
        if code.strip():
            HistoryService.save_scan(
                scan_id=result.analysis_id,
                target_name=safe_filename or f"snippet.{language.value}",
                scan_type="single_file",
                language=language.value,
                score=quality_score,
                lines_of_code=line_count,
                findings_count=len(all_findings),
                critical_security_count=security_report.critical_count,
                status=analysis_status.value,
                full_payload=result.model_dump(mode="json"),
            )

        return result

