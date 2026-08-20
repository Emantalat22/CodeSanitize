"""Multi-File Project Analysis Orchestrator."""

from datetime import datetime, timezone
import io
import os
import time
from typing import Dict, List, Tuple
import uuid
import zipfile
from app.analyzers.duplication_detector import DuplicationDetector
from app.analyzers.security import SecurityAnalyzer
from app.models.schemas import (
    CodeInput,
    DuplicationFinding,
    FileAnalysisSummary,
    ProjectAnalysisRequest,
    ProjectAnalysisResult,
    ProjectFileInput,
    SecurityReport,
    SupportedLanguage,
)
from app.parsers.language_detector import LanguageDetector
from app.parsers.registry import ParserRegistry
from app.services.analysis_service import AnalysisService
from app.services.history_service import HistoryService
from app.services.recommendation_service import RecommendationService

IGNORED_DIRS = {".git", ".svn", ".hg", "node_modules", "vendor", "__pycache__", "dist", "build", ".idea", ".vscode"}
SUPPORTED_EXTENSIONS = set(LanguageDetector.EXTENSION_MAP.keys())


class ProjectAnalysisService:
    """Orchestrates comprehensive multi-file codebase scans, metrics aggregation, and clone detection."""

    @classmethod
    def analyze_project(cls, request: ProjectAnalysisRequest) -> ProjectAnalysisResult:
        """Analyze a multi-file project payload."""
        start_time = time.perf_counter()
        project_id = str(uuid.uuid4())
        project_name = request.project_name or "Project Scan"

        files_to_analyze: List[ProjectFileInput] = request.files
        file_summaries: List[FileAnalysisSummary] = []
        files_for_duplication: List[Tuple[str, str, SupportedLanguage]] = []

        total_loc = 0
        lang_counts: Dict[str, int] = {}
        all_findings = []
        total_score_sum = 0

        for file_input in files_to_analyze:
            # Detect language
            lang = file_input.language
            if not lang or lang == SupportedLanguage.AUTO or str(lang).lower() == "auto":
                detected_lang = ParserRegistry.detect_language(file_input.code, file_input.filename)
            elif isinstance(lang, str):
                try:
                    detected_lang = SupportedLanguage(lang.lower())
                except Exception:
                    detected_lang = SupportedLanguage.PYTHON
            else:
                detected_lang = lang

            # Run single-file analysis
            code_res = AnalysisService.analyze(
                CodeInput(
                    code=file_input.code,
                    language=detected_lang,
                    filename=file_input.filename,
                    options=request.options,
                )
            )

            f_loc = code_res.metrics.lines_of_code
            total_loc += f_loc
            total_score_sum += code_res.quality_score
            all_findings.extend(code_res.findings)

            lang_name = detected_lang.value
            lang_counts[lang_name] = lang_counts.get(lang_name, 0) + f_loc

            file_summaries.append(
                FileAnalysisSummary(
                    filename=file_input.filename,
                    language=detected_lang,
                    lines_of_code=f_loc,
                    quality_score=code_res.quality_score,
                    complexity_level=code_res.complexity_report.complexity_level,
                    security_risk=code_res.security_report.risk_level,
                    findings_count=len(code_res.findings),
                    execution_time_ms=code_res.execution_time_ms,
                )
            )

            files_for_duplication.append((file_input.filename, file_input.code, detected_lang))

        # 2. Compute Language Distribution
        lang_dist: Dict[str, float] = {}
        if total_loc > 0:
            for l_name, l_loc in lang_counts.items():
                lang_dist[l_name] = round((l_loc / total_loc) * 100.0, 1)
        elif files_to_analyze:
            lang_dist["python"] = 100.0

        # 3. Detect Code Duplications
        duplications: List[DuplicationFinding] = DuplicationDetector.detect_duplications_in_files(
            files_for_duplication
        )

        # 4. Generate Security Summary
        security_summary: SecurityReport = SecurityAnalyzer.generate_report(all_findings)

        # 5. Calculate Overall Project Quality Score
        num_files = len(files_to_analyze)
        avg_score = round(total_score_sum / max(num_files, 1))
        # Deduct small penalty for project-wide duplications and critical security vulnerabilities
        dup_penalty = min(len(duplications) * 3, 15)
        crit_penalty = min(security_summary.critical_count * 20, 40)
        overall_score = max(avg_score - dup_penalty - crit_penalty, 0)

        # 6. Generate Project-Wide Recommendations
        recommendations = RecommendationService.generate_recommendations(
            findings=all_findings,
            security=security_summary,
            duplications=duplications,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        result = ProjectAnalysisResult(
            project_id=project_id,
            project_name=project_name,
            timestamp=datetime.now(timezone.utc),
            total_files=num_files,
            total_lines_of_code=total_loc,
            overall_quality_score=overall_score,
            language_distribution=lang_dist,
            security_summary=security_summary,
            files=file_summaries,
            duplications=duplications,
            recommendations=recommendations,
            execution_time_ms=round(elapsed_ms, 2),
        )

        # Save scan to local history
        HistoryService.save_scan(
            scan_id=project_id,
            target_name=project_name,
            scan_type="project",
            language=", ".join(lang_dist.keys()) or "multi",
            score=overall_score,
            lines_of_code=total_loc,
            findings_count=len(all_findings),
            critical_security_count=security_summary.critical_count,
            status="completed",
            full_payload=result.model_dump(mode="json"),
        )

        return result

    @classmethod
    def analyze_zip_archive(cls, zip_bytes: bytes, project_name: str = "Uploaded Project") -> ProjectAnalysisResult:
        """Extract source files from a ZIP archive and run full project intelligence scan."""
        files: List[ProjectFileInput] = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
                for file_info in z.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue

                    # Filter out hidden or ignored directory paths
                    parts = file_info.filename.replace("\\", "/").split("/")
                    if any(p in IGNORED_DIRS or p.startswith(".") for p in parts[:-1]):
                        continue

                    _, ext = os.path.splitext(file_info.filename.lower())
                    if ext in SUPPORTED_EXTENSIONS or ext in (".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"):
                        try:
                            file_bytes = z.read(file_info.filename)
                            # Skip large individual files (> 1MB)
                            if len(file_bytes) > 1024 * 1024:
                                continue
                            code_text = file_bytes.decode("utf-8", errors="replace")
                            files.append(
                                ProjectFileInput(
                                    filename=file_info.filename,
                                    code=code_text,
                                    language=SupportedLanguage.AUTO,
                                )
                            )
                        except Exception:
                            continue
        except Exception as e:
            # If invalid zip, return empty project
            pass

        return cls.analyze_project(
            ProjectAnalysisRequest(
                project_name=project_name,
                files=files,
            )
        )
