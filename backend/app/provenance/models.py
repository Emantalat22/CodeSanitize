"""Pydantic schemas and models for AI Code Provenance Analysis."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProvenanceSignal(BaseModel):
    """Specific static characteristic associated with synthetic or generated code patterns."""

    signal_type: str = Field(..., description="Classification category of the detected signal")
    severity: str = Field("medium", description="Signal severity: 'low', 'medium', 'high'")
    confidence: float = Field(1.0, description="Confidence score between 0.0 and 1.0")
    description: str = Field(..., description="Human-readable explanation of why this pattern was flagged")
    file_location: Optional[Dict[str, Any]] = Field(None, description="Line number and column span")
    evidence: Optional[str] = Field(None, description="Code snippet or comment text showing the pattern")


class CommentAnalysisResult(BaseModel):
    """Analysis of code comments, redundant descriptions, and boilerplate patterns."""

    total_comments: int = 0
    redundant_comments_count: int = 0
    obvious_comments: List[ProvenanceSignal] = Field(default_factory=list)
    comment_ratio: float = 0.0


class IdentifierAnalysisResult(BaseModel):
    """Analysis of variable naming conventions, generic tokens, and structural naming patterns."""

    generic_identifiers_count: int = 0
    generic_identifiers: List[ProvenanceSignal] = Field(default_factory=list)
    repeated_naming_patterns: List[str] = Field(default_factory=list)


class StyleAnalysisResult(BaseModel):
    """Analysis of code structure, formatting symmetry, and template regularities."""

    uniformity_score: float = 0.0
    excessive_regularity: bool = False
    signals: List[ProvenanceSignal] = Field(default_factory=list)


class ProvenanceReport(BaseModel):
    """Comprehensive AI-generated code provenance and stylistic characteristic report."""

    provenance_score: int = Field(
        ...,
        description="Deterministic score (0-100) indicating density of synthetic/generated code traits",
    )
    ai_pattern_score: int = Field(
        default=0,
        description="Dedicated AI Pattern Score (0-100)",
    )
    confidence_level: str = Field("medium", description="'low', 'medium', 'high'")
    confidence_score: float = Field(0.85, description="Confidence rating between 0.0 and 1.0")
    risk_level: str = Field("low", description="'low', 'medium', 'high'")
    signals_detected: List[ProvenanceSignal] = Field(default_factory=list)
    detected_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    ai_pattern_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comment_analysis: CommentAnalysisResult = Field(default_factory=CommentAnalysisResult)
    identifier_analysis: IdentifierAnalysisResult = Field(default_factory=IdentifierAnalysisResult)
    style_analysis: StyleAnalysisResult = Field(default_factory=StyleAnalysisResult)
    recommendations: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(0.0, description="Analysis latency in ms")


