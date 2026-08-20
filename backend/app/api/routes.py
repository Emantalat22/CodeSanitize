"""API Route handlers for CodeSanitize."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from app.models.schemas import (
    AnalysisResult,
    CodeInput,
    HealthResponse,
    LanguageInfo,
    ProjectAnalysisRequest,
    ProjectAnalysisResult,
    ScanHistorySummary,
    SupportedLanguage,
    TransformationResult,
    TransformationRuleSpec,
    ValidateRequest,
    ValidationResult,
)
from app.provenance.models import ProvenanceReport
from app.services.analysis_service import AnalysisService

from app.services.health_service import HealthService
from app.services.history_service import HistoryService
from app.services.project_service import ProjectAnalysisService
from app.services.report_service import ReportService
from app.services.transformation_engine import TransformationEngine
from app.transformers.registry import TransformationRegistry
from app.validators.pipeline import ValidationPipeline

router = APIRouter()


# ===================================================
# 1. System & Capabilities Endpoints
# ===================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current operational status, application version, and environment.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Return backend service health status."""
    return HealthService.get_health()


@router.get(
    "/languages",
    response_model=List[LanguageInfo],
    summary="List Supported Languages",
    description="Returns supported programming languages and their parser availability.",
    tags=["Capabilities"],
)
async def list_languages() -> List[LanguageInfo]:
    """Return list of supported languages and AST capabilities."""
    return HealthService.get_supported_languages()


# ===================================================
# 2. Single-File Code Intelligence Analysis
# ===================================================

@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyze Source Code",
    description="Executes deterministic AST parsing, metrics collection, intelligence findings, and quality scoring.",
    tags=["Analysis"],
    status_code=status.HTTP_200_OK,
)
async def analyze_code(payload: CodeInput) -> AnalysisResult:
    """Analyze source code without executing it."""
    return AnalysisService.analyze(payload)


@router.post(
    "/provenance",
    response_model=ProvenanceReport,
    summary="Analyze Code Provenance Patterns",
    description="Executes deterministic static inspection of AI-style/synthetic patterns.",
    tags=["Provenance"],
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/provenance/analyze",
    response_model=ProvenanceReport,
    summary="Analyze Code Provenance Patterns",
    description="Executes deterministic static inspection of AI-style/synthetic patterns (redundant comments, formulaic identifiers, formatting regularity).",
    tags=["Provenance"],
    status_code=status.HTTP_200_OK,
)
async def analyze_provenance(payload: CodeInput) -> ProvenanceReport:
    """Analyze AI-style provenance and synthetic patterns without executing code."""
    from app.provenance.provenance_service import ProvenanceService
    return ProvenanceService.analyze_provenance(payload)




# ===================================================
# 3. Multi-File Project Analysis & ZIP Upload
# ===================================================

@router.post(
    "/project/analyze",
    response_model=ProjectAnalysisResult,
    summary="Analyze Multi-File Project",
    description="Analyzes multiple source code files, aggregates project metrics, detects duplications, and generates recommendations.",
    tags=["Project Analysis"],
    status_code=status.HTTP_200_OK,
)
async def analyze_project(payload: ProjectAnalysisRequest) -> ProjectAnalysisResult:
    """Analyze multi-file project codebase payload."""
    return ProjectAnalysisService.analyze_project(payload)


@router.post(
    "/project/upload",
    response_model=ProjectAnalysisResult,
    summary="Analyze Project ZIP Archive",
    description="Upload a ZIP archive to analyze all contained source files, aggregate metrics, and detect code duplications.",
    tags=["Project Analysis"],
    status_code=status.HTTP_200_OK,
)
async def upload_project_zip(
    file: UploadFile = File(..., description="ZIP archive containing source code project"),
    project_name: Optional[str] = Query(None, description="Optional custom project name"),
) -> ProjectAnalysisResult:
    """Analyze uploaded ZIP archive without executing any code."""
    contents = await file.read()
    p_name = project_name or file.filename or "Uploaded Project"
    return ProjectAnalysisService.analyze_zip_archive(contents, project_name=p_name)


# ===================================================
# 4. Semantics-Preserving Transformation
# ===================================================

@router.get(
    "/transformations",
    response_model=List[TransformationRuleSpec],
    summary="List Transformation Rules",
    description="Returns available semantics-preserving transformation rules.",
    tags=["Transformation"],
)
async def list_transformations(
    language: Optional[SupportedLanguage] = Query(None, description="Filter rules by target language")
) -> List[TransformationRuleSpec]:
    """Return available transformation rule specifications."""
    return TransformationRegistry.list_rule_specs(language)


@router.post(
    "/transform",
    response_model=TransformationResult,
    summary="Transform Source Code Safely",
    description="Applies deterministic, semantics-preserving transformations with pre-acceptance validation.",
    tags=["Transformation"],
    status_code=status.HTTP_200_OK,
)
async def transform_code(payload: CodeInput) -> TransformationResult:
    """Transform source code safely without executing it."""
    return TransformationEngine.transform(payload)


# ===================================================
# 5. Multi-Stage Pre-Acceptance Validation
# ===================================================

@router.post(
    "/validate",
    response_model=ValidationResult,
    summary="Validate Transformation Equivalence",
    description="Executes multi-stage pre-acceptance validation on candidate transformed code.",
    tags=["Validation"],
    status_code=status.HTTP_200_OK,
)
async def validate_code(payload: ValidateRequest) -> ValidationResult:
    """Validate transformed code against original baseline without executing code."""
    pipeline = ValidationPipeline()
    return pipeline.validate(
        orig_code=payload.original_code,
        trans_code=payload.transformed_code,
        policy=payload.policy,
        options=payload.options,
    )


# ===================================================
# 6. Analysis History & Persistence
# ===================================================

@router.get(
    "/history",
    response_model=List[ScanHistorySummary],
    summary="List Analysis Scan History",
    description="Returns recent single-file and project scans stored in local history.",
    tags=["History"],
)
async def list_history(
    limit: int = Query(50, ge=1, le=200, description="Max history records to return")
) -> List[ScanHistorySummary]:
    """Retrieve local scan history summaries."""
    return HistoryService.list_scans(limit=limit)


@router.get(
    "/history/{scan_id}",
    summary="Get Scan Details from History",
    description="Retrieve full details for a past scan by scan ID.",
    tags=["History"],
)
async def get_history_scan(scan_id: str):
    """Retrieve full analysis report for a specific scan."""
    data = HistoryService.get_scan(scan_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan ID '{scan_id}' not found in local history.",
        )
    return data


@router.delete(
    "/history/{scan_id}",
    summary="Delete Scan from History",
    description="Delete a specific scan record from local history.",
    tags=["History"],
)
async def delete_history_scan(scan_id: str):
    """Delete a scan record."""
    success = HistoryService.delete_scan(scan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan ID '{scan_id}' not found in history.",
        )
    return {"message": f"Scan '{scan_id}' deleted successfully."}


@router.delete(
    "/history",
    summary="Clear All Scan History",
    description="Clear all analysis scan history records.",
    tags=["History"],
)
async def clear_history():
    """Clear all analysis history."""
    HistoryService.clear_history()
    return {"message": "Analysis history cleared successfully."}


# ===================================================
# 7. Report Generation & Export Endpoints
# ===================================================

@router.get(
    "/reports/{scan_id}/json",
    summary="Export Scan as JSON Report",
    description="Export a past scan result as formatted JSON.",
    tags=["Reports"],
)
async def export_json_report(scan_id: str):
    """Export scan as JSON."""
    data = HistoryService.get_scan(scan_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan ID '{scan_id}' not found in history.",
        )
    return data


@router.get(
    "/reports/{scan_id}/html",
    summary="Export Scan as HTML Report",
    description="Export a past scan result as a clean, print-ready HTML dashboard.",
    tags=["Reports"],
)
async def export_html_report(scan_id: str):
    """Export scan as print-ready HTML."""
    data = HistoryService.get_scan(scan_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan ID '{scan_id}' not found in history.",
        )
    html_content = ReportService.generate_html_report(data)
    return Response(content=html_content, media_type="text/html")


@router.get(
    "/reports/{scan_id}/pdf",
    summary="Export Scan as Printable PDF Report",
    description="Export a past scan result as a downloadable PDF-compatible document.",
    tags=["Reports"],
)
async def export_pdf_report(scan_id: str):
    """Export scan as downloadable PDF report."""
    data = HistoryService.get_scan(scan_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan ID '{scan_id}' not found in history.",
        )
    pdf_content = ReportService.generate_pdf_report(data)
    headers = {"Content-Disposition": f"attachment; filename=codesanitize_report_{scan_id[:8]}.html"}
    return Response(content=pdf_content, media_type="application/octet-stream", headers=headers)


@router.post(
    "/reports/export/html",
    summary="Direct Export HTML Report",
    description="Render a live analysis payload into a standalone HTML report.",
    tags=["Reports"],
)
async def export_direct_html_report(payload: Dict[str, Any]):
    """Render direct HTML report."""
    html_content = ReportService.generate_html_report(payload)
    return Response(content=html_content, media_type="text/html")


@router.post(
    "/reports/export/json",
    summary="Direct Export JSON Report",
    description="Format a live analysis payload into a downloadable JSON report.",
    tags=["Reports"],
)
async def export_direct_json_report(payload: Dict[str, Any]):
    """Format direct JSON report."""
    json_str = ReportService.generate_json_report(payload)
    return Response(content=json_str, media_type="application/json")
