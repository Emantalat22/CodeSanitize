"""Pydantic schemas and data contracts for CodeSanitize."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    C = "c"
    AUTO = "auto"



class PipelineStatus(str, Enum):
    """Module implementation readiness status."""

    AVAILABLE = "available"
    IN_DEVELOPMENT = "in_development"
    PLANNED = "planned"


class AnalysisStatus(str, Enum):
    """Execution status of code analysis."""

    COMPLETED = "completed"
    SYNTAX_ERROR = "syntax_error"
    PARSER_UNAVAILABLE = "parser_unavailable"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    FAILED = "failed"


class TransformationStatus(str, Enum):
    """Execution status of semantics-preserving transformation."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    NO_CHANGES_APPLIED = "no_changes_applied"
    REJECTED = "rejected"
    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    FAILED = "failed"


class TransformationSafetyLevel(str, Enum):
    """Safety classification for transformation rules."""

    SAFE_CONSERVATIVE = "safe_conservative"
    SAFE_STRUCTURAL = "safe_structural"
    EXPERIMENTAL = "experimental"


class TransformationAttemptStatus(str, Enum):
    """Outcome status of an individual transformation attempt."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ValidationVerdict(str, Enum):
    """Outcome verdict of pre-acceptance validation."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ValidationPolicy(str, Enum):
    """Pre-acceptance validation enforcement policy."""

    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


class ValidationConfidenceLevel(str, Enum):
    """Confidence rating in behavioral equivalence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ValidationRiskFlag(str, Enum):
    """Specific risk categories detected during validation."""

    REFLECTION_DETECTED = "reflection_detected"
    EVAL_EXEC_DETECTED = "eval_exec_detected"
    DYNAMIC_ATTRIBUTE_ACCESS = "dynamic_attribute_access"
    DYNAMIC_IMPORT = "dynamic_import"
    SIDE_EFFECT_FILE_IO = "side_effect_file_io"
    SIDE_EFFECT_SUBPROCESS = "side_effect_subprocess"
    SIDE_EFFECT_NETWORK = "side_effect_network"
    SIDE_EFFECT_ENV = "side_effect_env"
    SIDE_EFFECT_RANDOM_TIME = "side_effect_random_time"
    SIDE_EFFECT_THREADING = "side_effect_threading"


class IssueSeverity(str, Enum):
    """Severity levels for analysis diagnostics (legacy)."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FindingSeverity(str, Enum):
    """Severity classification for static analysis findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(str, Enum):
    """Domain category of static analysis finding."""

    QUALITY = "quality"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    STRUCTURE = "structure"
    NON_FUNCTIONAL = "non_functional"
    SIMILARITY = "similarity"


class FindingLocation(BaseModel):
    """Source code location for an analysis finding."""

    line_start: Optional[int] = Field(None, description="1-indexed starting line")
    line_end: Optional[int] = Field(None, description="1-indexed ending line")
    column_start: Optional[int] = Field(None, description="1-indexed starting column")
    column_end: Optional[int] = Field(None, description="1-indexed ending column")
    function_name: Optional[str] = Field(None, description="Enclosing function name if applicable")


class AnalysisFinding(BaseModel):
    """Structured code intelligence finding or diagnostic."""

    id: str = Field(..., description="Unique finding ID (e.g. SEC-EVAL-01)")
    category: FindingCategory = Field(..., description="Finding category")
    severity: FindingSeverity = Field(..., description="Severity level")
    title: str = Field(..., description="Short finding summary")
    description: str = Field(..., description="Detailed explanation of finding")
    location: Optional[FindingLocation] = Field(None, description="Source location")
    evidence: Optional[str] = Field(None, description="Relevant code snippet or token evidence")
    recommendation: Optional[str] = Field(None, description="Actionable recommendation for improvement")


class ComplexityFunctionMetric(BaseModel):
    """Complexity and nesting statistics for an individual function."""

    name: str = Field(..., description="Function or method name")
    line_start: int = Field(..., description="1-indexed line number")
    cyclomatic_complexity: int = Field(1, description="Calculated McCabe cyclomatic complexity")
    nesting_depth: int = Field(1, description="Maximum nesting depth within function")
    statement_count: int = Field(0, description="Total statements in function body")


class ComplexityMetrics(BaseModel):
    """Calculated cyclomatic complexity and branching metrics."""

    cyclomatic_complexity: int = Field(1, description="Overall McCabe complexity")
    branching_count: int = Field(0, description="Total branching statements (if/elif/else/match)")
    loop_count: int = Field(0, description="Total loop statements (for/while)")
    max_nesting_depth: int = Field(0, description="Maximum block nesting depth")
    exception_handling_count: int = Field(0, description="Total try/except blocks")
    function_complexities: List[ComplexityFunctionMetric] = Field(
        default_factory=list,
        description="Per-function complexity breakdown",
    )


class StructuralFingerprint(BaseModel):
    """Identifier-independent structural and AST fingerprint."""

    ast_node_hash: str = Field(..., description="SHA-256 hash of normalized AST node type sequence")
    control_flow_fingerprint: str = Field(..., description="Hash of control flow topology")
    structure_vector: List[int] = Field(
        default_factory=list,
        description="Vector representation of structural feature frequencies",
    )
    normalized_skeleton: str = Field(..., description="Token-agnostic structural skeleton")


class SimilarityScore(BaseModel):
    """Calculated structural similarity compared to canonical baselines."""

    score: float = Field(..., ge=0.0, le=100.0, description="Similarity score (0-100)")
    confidence: str = Field(default="high", description="Estimation confidence")
    explanation: str = Field(..., description="Human-readable explanation of structural similarity")


class AnalyzerReport(BaseModel):
    """Summary execution report from an individual registered analyzer module."""

    analyzer_id: str = Field(..., description="Unique analyzer ID")
    analyzer_name: str = Field(..., description="Analyzer module name")
    execution_time_ms: float = Field(0.0, description="Execution time in milliseconds")
    status: str = Field(default="completed", description="Execution status")
    findings_count: int = Field(0, description="Count of findings generated")
    findings: List[AnalysisFinding] = Field(
        default_factory=list,
        description="Findings produced by this analyzer",
    )


class LanguageInfo(BaseModel):
    """Metadata describing a supported language and parser capability."""

    id: SupportedLanguage
    display_name: str
    extensions: List[str]
    ast_parser: str
    status: PipelineStatus


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="ok", description="Current health status of the service")
    app: str = Field(default="CodeSanitize", description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Runtime environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )


class CodeInput(BaseModel):
    """Source code input schema for analysis and transformation."""

    code: str = Field(..., description="Raw source code content")
    language: SupportedLanguage = Field(
        default=SupportedLanguage.AUTO,
        description="Source code programming language or 'auto' for automatic detection",
    )
    filename: Optional[str] = Field(None, max_length=255, description="Optional filename or virtual path")
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible analyzer/transformer options and rule configurations",
    )
    human_authored_mode: bool = Field(
        default=True,
        description="Prioritize natural developer style over preserving artificial AI boilerplate formatting",
    )




class AnalysisIssue(BaseModel):
    """Structured code issue or syntax/parser diagnostic (legacy compatibility)."""

    rule_id: str = Field(..., description="Unique identifier of the diagnostic rule or parser error")
    message: str = Field(..., description="Human-readable diagnostic description")
    severity: IssueSeverity = Field(default=IssueSeverity.WARNING, description="Diagnostic severity")
    line_start: Optional[int] = Field(None, description="1-indexed starting line number")
    line_end: Optional[int] = Field(None, description="1-indexed ending line number")
    column_start: Optional[int] = Field(None, description="1-indexed starting column")
    column_end: Optional[int] = Field(None, description="1-indexed ending column")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or token snippet")


class ComplexityFunction(BaseModel):
    """Complexity ranking and statistics for an individual function."""

    name: str = Field(..., description="Function or method name")
    complexity: int = Field(1, description="McCabe cyclomatic complexity score")
    risk: str = Field("low", description="Risk tier: low, medium, high")
    line_start: int = Field(1, description="1-indexed starting line")
    nesting_depth: int = Field(1, description="Maximum nesting depth within function")
    statement_count: int = Field(0, description="Total statements in function body")


class ComplexityReport(BaseModel):
    """Holistic complexity report for module and functions."""

    average_complexity: float = Field(1.0, description="Average cyclomatic complexity across functions")
    maximum_complexity: int = Field(1, description="Maximum cyclomatic complexity in any single function")
    most_complex_functions: List[ComplexityFunction] = Field(
        default_factory=list,
        description="Ranked list of complex functions",
    )
    complexity_level: str = Field("Low", description="Overall complexity tier: Low, Medium, High")
    cyclomatic_complexity: int = Field(1, description="Overall McCabe module complexity")
    branching_count: int = Field(0, description="Total branching statements")
    loop_count: int = Field(0, description="Total loop statements")
    max_nesting_depth: int = Field(0, description="Maximum block nesting depth")
    exception_handling_count: int = Field(0, description="Total try/except blocks")
    function_complexities: List[ComplexityFunctionMetric] = Field(
        default_factory=list,
        description="Per-function complexity breakdown",
    )


class SecurityReport(BaseModel):
    """Aggregated static security findings report."""

    critical_count: int = Field(0, description="Count of critical security issues")
    warning_count: int = Field(0, description="Count of warning/high/medium security issues")
    informational_count: int = Field(0, description="Count of low/info security issues")
    risk_level: str = Field("Clean", description="Security risk rating: Clean, Low, Medium, High, Critical")
    findings: List[AnalysisFinding] = Field(
        default_factory=list,
        description="List of security findings",
    )


class CodeMetrics(BaseModel):
    """Calculated structural and AST metrics from actual parsing."""

    lines_of_code: int = Field(0, description="Total physical lines of code")
    blank_lines: int = Field(0, description="Total blank lines")
    comment_lines: int = Field(0, description="Total single/multi-line comment lines")
    function_count: int = Field(0, description="Number of function or method definitions")
    class_count: int = Field(0, description="Number of class declarations")
    import_count: int = Field(0, description="Number of module import statements")
    average_function_length: float = Field(0.0, description="Average lines or statements per function")
    raw_character_count: int = Field(0, description="Raw character count")
    ast_nodes_count: int = Field(0, description="Total count of AST nodes in parse tree")
    variable_assignment_count: int = Field(0, description="Number of variable assignments")
    control_flow_node_count: int = Field(0, description="Number of control flow statements")
    max_nesting_depth: int = Field(0, description="Maximum nesting depth")
    cyclomatic_complexity: int = Field(1, description="Calculated McCabe complexity")
    comment_count: int = Field(0, description="Count of comments detected")
    docstring_count: int = Field(0, description="Count of docstrings detected")
    comment_ratio: float = Field(0.0, description="Ratio of comments/docstrings to total lines")


# StructuralMetrics is an alias for CodeMetrics for backward compatibility
StructuralMetrics = CodeMetrics


class ArtifactCategory(str, Enum):
    """Category of non-functional artifacts."""

    WHITESPACE = "whitespace"
    UNICODE = "unicode"
    COMMENTS = "comments"
    FORMATTING = "formatting"
    ENCODING = "encoding"


class NonFunctionalArtifact(BaseModel):
    """Detected non-functional source code formatting/structural artifact."""

    category: ArtifactCategory = Field(..., description="Artifact category")
    kind: str = Field(..., description="Specific artifact identifier (e.g. trailing_whitespace, unusual_unicode)")
    description: str = Field(..., description="Human-readable description of detected artifact")
    line_number: Optional[int] = Field(None, description="1-indexed line number if localized")
    column_number: Optional[int] = Field(None, description="1-indexed column number if localized")
    character: Optional[str] = Field(None, description="The raw character or substring detected")
    unicode_code_point: Optional[str] = Field(None, description="Unicode code point representation (e.g. U+200B)")
    count: int = Field(1, description="Number of occurrences")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual properties")


class ParserCapabilities(BaseModel):
    """Features supported by the parser used for analysis."""

    ast_available: bool = Field(..., description="Whether true AST generation is available for this language")
    syntax_validation: bool = Field(..., description="Whether syntax validation is supported")
    metrics_collection: bool = Field(..., description="Whether structural metrics are computed")
    non_functional_detection: bool = Field(..., description="Whether non-functional artifacts were analyzed")
    engine_name: str = Field(..., description="Name of underlying parser engine")


class AnalysisResult(BaseModel):
    """Comprehensive structured report of AST, intelligence, and static analysis."""

    analysis_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this analysis run",
    )
    language: SupportedLanguage = Field(..., description="Target programming language")
    filename: Optional[str] = Field(None, description="Source filename if provided")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of analysis run",
    )
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the analysis execution",
    )
    quality_score: int = Field(100, ge=0, le=100, description="Deterministic code quality score (0-100)")
    overall_score: int = Field(100, ge=0, le=100, description="Overall health score (0-100, alias)")
    metrics: CodeMetrics = Field(
        default_factory=CodeMetrics,
        description="Calculated physical and AST code metrics",
    )
    structural_metrics: CodeMetrics = Field(
        default_factory=CodeMetrics,
        description="Calculated AST and structural metrics (alias)",
    )
    complexity_report: ComplexityReport = Field(
        default_factory=ComplexityReport,
        description="Detailed cyclomatic complexity and function ranking report",
    )
    complexity_metrics: ComplexityMetrics = Field(
        default_factory=ComplexityMetrics,
        description="Calculated McCabe complexity and branching breakdown (alias)",
    )
    security_report: SecurityReport = Field(
        default_factory=SecurityReport,
        description="Aggregated security findings report",
    )
    findings: List[AnalysisFinding] = Field(
        default_factory=list,
        description="Structured code intelligence and security findings",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable refactoring and security recommendations",
    )
    code_length: int = Field(0, description="Total character length of analyzed source code")
    line_count: int = Field(0, description="Total lines of code")
    syntax_valid: bool = Field(True, description="Whether source code parsed into a valid AST")
    parser_used: str = Field("ast", description="Identifier of the parser used")
    analysis_status: AnalysisStatus = Field(AnalysisStatus.COMPLETED, description="Overall status of analysis")
    issues: List[AnalysisIssue] = Field(default_factory=list, description="Syntax errors and parser diagnostics")
    detected_nonfunctional_artifacts: List[NonFunctionalArtifact] = Field(
        default_factory=list,
        description="List of detected non-functional formatting and character artifacts",
    )
    fingerprint: Optional[StructuralFingerprint] = Field(
        None,
        description="Identifier-independent structural AST fingerprint",
    )
    analyzer_reports: List[AnalyzerReport] = Field(
        default_factory=list,
        description="Individual execution reports from registered analyzers",
    )
    detected_patterns: List[str] = Field(
        default_factory=list,
        description="List of detected algorithmic or structural patterns",
    )
    risk_categories: List[str] = Field(
        default_factory=list,
        description="Categorized risk tags identified during analysis",
    )
    capabilities: ParserCapabilities = Field(..., description="Parser capability manifest")
    execution_time_ms: float = Field(0.0, description="Analysis elapsed time in milliseconds")



class TransformationRuleSpec(BaseModel):
    """Specification of an available or applied transformation rule."""

    rule_id: str = Field(..., description="Unique rule identifier (e.g. PY-FMT-NORM-01)")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Explanation of semantics-preserving changes made")
    supported_languages: List[SupportedLanguage] = Field(
        default_factory=list,
        description="Languages compatible with this rule",
    )
    safety_level: TransformationSafetyLevel = Field(
        default=TransformationSafetyLevel.SAFE_CONSERVATIVE,
        description="Rule safety classification",
    )
    default_enabled: bool = Field(True, description="Whether rule is active by default")


class TransformationAttempt(BaseModel):
    """Detailed record of an individual transformation rule application."""

    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    status: TransformationAttemptStatus = Field(..., description="Whether rule was accepted or rejected")
    reason: Optional[str] = Field(None, description="Reason for rejection or skipping if applicable")
    changes_description: Optional[str] = Field(None, description="Summary of modifications performed")
    change_count: int = Field(0, description="Count of changes made by this step")
    validation_verdict: ValidationVerdict = Field(
        default=ValidationVerdict.PASSED,
        description="Validation outcome for this specific step",
    )
    validation_message: Optional[str] = Field(None, description="Validation diagnostic feedback")


class DiffSummary(BaseModel):
    """Summary metrics of source code diff."""

    additions: int = Field(0, description="Count of inserted lines")
    removals: int = Field(0, description="Count of deleted lines")
    changed_lines: int = Field(0, description="Total count of modified lines")


class ValidationDiagnostic(BaseModel):
    """Validation check diagnostic (backward compatibility model)."""

    check_name: str = Field(..., description="Name of validation pass")
    passed: bool = Field(..., description="Whether this validation check passed")
    details: str = Field(..., description="Explanation of validation outcome")


class ValidationCheckResult(BaseModel):
    """Structured result of an individual validator check pass."""

    check_name: str = Field(..., description="Validator name (e.g. Syntax, Public Interface, Control Flow)")
    passed: bool = Field(..., description="Whether check passed without error")
    severity: ValidationVerdict = Field(..., description="PASSED, WARNING, or FAILED")
    details: str = Field(..., description="Detailed diagnostic description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic context metadata")


class ValidationTestCase(BaseModel):
    """Reusable specification for validation test cases."""

    test_id: str = Field(..., description="Unique test case identifier")
    description: str = Field(..., description="Description of test scenario")
    input_values: Dict[str, Any] = Field(default_factory=dict, description="Test input parameters")
    expected_output: Optional[Any] = Field(None, description="Expected return value")
    expected_exception: Optional[str] = Field(None, description="Expected exception class if failure expected")


class ValidationResult(BaseModel):
    """Comprehensive multi-stage validation report."""

    is_valid: bool = Field(..., description="Overall validation acceptance status")
    verdict: ValidationVerdict = Field(default=ValidationVerdict.PASSED, description="Validation verdict status")
    confidence_level: ValidationConfidenceLevel = Field(
        default=ValidationConfidenceLevel.HIGH,
        description="Estimated confidence in behavioral equivalence",
    )
    policy_applied: ValidationPolicy = Field(
        default=ValidationPolicy.STRICT,
        description="Validation policy applied (strict, balanced, permissive)",
    )
    syntax_valid: bool = Field(..., description="Whether transformed code parsed without syntax errors")
    semantic_invariants_preserved: bool = Field(
        ...,
        description="Whether public interfaces, control flow, and data flow remain invariant",
    )
    validators_run: List[str] = Field(
        default_factory=list,
        description="List of validator stages executed in the pipeline",
    )
    passed_checks: List[ValidationCheckResult] = Field(
        default_factory=list,
        description="List of passed validation checks",
    )
    warnings: List[ValidationCheckResult] = Field(
        default_factory=list,
        description="List of warning checks flagged by validators",
    )
    failures: List[ValidationCheckResult] = Field(
        default_factory=list,
        description="List of concrete validation check failures",
    )
    diagnostics: List[ValidationDiagnostic] = Field(
        default_factory=list,
        description="Flattened diagnostics list for legacy compatibility",
    )
    structural_changes: List[str] = Field(
        default_factory=list,
        description="Approved structural changes detected",
    )
    interface_changes: List[str] = Field(
        default_factory=list,
        description="Detected interface or signature mutations",
    )
    risk_flags: List[ValidationRiskFlag] = Field(
        default_factory=list,
        description="Active risk categories (e.g. reflection, side effects)",
    )
    test_cases: List[ValidationTestCase] = Field(
        default_factory=list,
        description="Structured test case definitions",
    )
    message: str = Field(..., description="Summary message of validation status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the validation run",
    )


class ValidateRequest(BaseModel):
    """Request payload for standalone POST /api/validate endpoint."""

    original_code: str = Field(..., description="Original baseline source code")
    transformed_code: str = Field(..., description="Transformed candidate source code")
    language: SupportedLanguage = Field(default=SupportedLanguage.PYTHON, description="Target language")
    filename: Optional[str] = Field(None, description="Optional filename")
    policy: ValidationPolicy = Field(
        default=ValidationPolicy.STRICT,
        description="Enforcement policy (strict, balanced, permissive)",
    )
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional validator options")


class FingerprintRemediationPreview(BaseModel):
    """Preview of detected AI watermark fingerprint and its automated remediation fix."""
    fingerprint_type: str = Field(..., description="Category of detected watermark (comment, identifier, structure, formatting)")
    detected_fingerprint: str = Field(..., description="What specific watermark/fingerprint was detected")
    applied_fix: str = Field(..., description="What transformation safely removed the fingerprint")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence rating of the automated fix (0.0 - 1.0)")
    location: Optional[str] = Field(None, description="Line number or scope location where watermark appeared")
    remediation_rule: str = Field(..., description="Rule ID that executed the remediation (e.g. PROV-COMMENT-NORM-01)")


class TransformationResult(BaseModel):
    """Structured result of semantics-preserving transformation with automated watermark remediation."""


    transformation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this transformation run",
    )
    language: SupportedLanguage = Field(..., description="Target programming language")
    filename: Optional[str] = Field(None, description="Source filename if provided")
    original_code: str = Field(..., description="Original input source code")
    transformed_code: str = Field(..., description="Safely normalized/transformed source code")
    transformation_status: TransformationStatus = Field(
        ...,
        description="Overall transformation status",
    )
    transformations_applied: List[TransformationAttempt] = Field(
        default_factory=list,
        description="List of transformation rules safely applied and accepted",
    )
    rejected_transformations: List[TransformationAttempt] = Field(
        default_factory=list,
        description="List of transformation rules that were rejected during validation",
    )
    attempt_history: List[TransformationAttempt] = Field(
        default_factory=list,
        description="Chronological history of all attempted transformations with verdicts",
    )
    change_count: int = Field(0, description="Total count of accepted modifications")
    diff: Optional[str] = Field(None, description="Unified diff representation of changes")
    diff_summary: DiffSummary = Field(
        default_factory=DiffSummary,
        description="Diff statistics breakdown",
    )
    validation_status: ValidationVerdict = Field(
        default=ValidationVerdict.PASSED,
        description="Overall pre-acceptance validation verdict",
    )
    validation_report: Optional[ValidationResult] = Field(
        None,
        description="Comprehensive multi-stage validation report",
    )
    original_ai_score: Optional[int] = Field(
        None,
        description="AI Pattern Score of original code (0-100)",
    )
    transformed_ai_score: Optional[int] = Field(
        None,
        description="AI Pattern Score of normalized code (0-100)",
    )
    reduction_percentage: Optional[float] = Field(
        None,
        description="Percentage reduction in AI/synthetic pattern score",
    )
    comments_removed: int = Field(0, description="Total count of synthetic/redundant comments removed")
    identifiers_changed: int = Field(0, description="Total count of generic identifiers renamed into meaningful human names")
    structural_patterns_changed: int = Field(0, description="Total count of structural and dictionary simplifications applied")
    redundant_logic_removed: int = Field(0, description="Total count of redundant intermediate assignments/returns removed")
    formatting_fixes: int = Field(0, description="Total count of formatting and whitespace fixes applied")
    remediations_applied: List[FingerprintRemediationPreview] = Field(
        default_factory=list,
        description="List of detected watermarks and their applied automated fixes with confidence ratings",
    )
    removed_patterns: List[str] = Field(
        default_factory=list,
        description="List of AI/synthetic pattern categories successfully removed during transformation",
    )
    pattern_explanations: List[str] = Field(
        default_factory=list,
        description="Human-readable explanations for each applied modification",
    )
    pattern_categories_changed: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of modifications by category (comments, identifiers, structures, formatting)",
    )
    remediation_passes_count: int = Field(
        1,
        description="Number of iterative remediation passes executed to eliminate residual fingerprints",
    )
    fingerprint_rescan_report: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed multi-layer rescan report verifying zero remaining AI fingerprints",
    )
    human_authored_mode: bool = Field(
        default=True,
        description="Whether aggressive Human Authored Mode normalization was applied",
    )
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or caveats")


    execution_time_ms: float = Field(0.0, description="Transformation execution time in ms")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of transformation run",
    )





# ===================================================
# Chunk 7: Duplication, Project Analysis & History Schemas
# ===================================================

class DuplicationLocation(BaseModel):
    """File line span location for a duplicated code block."""

    filename: str = Field(..., description="Source file containing the duplicated block")
    line_start: int = Field(..., description="1-indexed starting line number")
    line_end: int = Field(..., description="1-indexed ending line number")
    function_name: Optional[str] = Field(None, description="Enclosing function or method name if applicable")


class DuplicationFinding(BaseModel):
    """Structured code clone or duplication detection finding."""

    id: str = Field(
        default_factory=lambda: f"DUP-{uuid.uuid4().hex[:8].upper()}",
        description="Unique identifier for this clone instance",
    )
    similarity_percentage: float = Field(..., description="Calculated similarity percentage (0-100%)")
    primary_location: DuplicationLocation = Field(..., description="Primary reference occurrence")
    duplicate_location: DuplicationLocation = Field(..., description="Duplicated occurrence")
    duplicate_type: str = Field(
        default="exact_function",
        description="Clone classification: 'exact_function', 'structural_clone', 'token_sequence'",
    )
    snippet_preview: Optional[str] = Field(None, description="Preview of duplicated code snippet")
    recommendation: str = Field(
        default="Extract duplicate logic into a shared reusable utility function or module.",
        description="Refactoring recommendation for DRY compliance",
    )


class ProjectFileInput(BaseModel):
    """Single file within a multi-file project analysis request."""

    filename: str = Field(..., description="Relative or absolute filepath within the project")
    code: str = Field(..., description="Source code text of the file")
    language: Optional[SupportedLanguage | str] = Field(
        default=SupportedLanguage.AUTO,
        description="File programming language or 'auto' for automatic detection",
    )


class ProjectAnalysisRequest(BaseModel):
    """Multi-file project scan input payload."""

    project_name: str = Field(default="Project", description="Display name for the project")
    files: List[ProjectFileInput] = Field(..., description="List of source code files to analyze")
    options: Dict[str, Any] = Field(default_factory=dict, description="Custom analysis options")


class FileAnalysisSummary(BaseModel):
    """Per-file summary inside a project-level analysis result."""

    filename: str
    language: SupportedLanguage
    lines_of_code: int = 0
    quality_score: int = 0
    complexity_level: str = "Low"
    security_risk: str = "Clean"
    findings_count: int = 0
    execution_time_ms: float = 0.0


class ProjectAnalysisResult(BaseModel):
    """Comprehensive project-level analysis report across multiple files."""

    project_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this project scan",
    )
    project_name: str = Field(..., description="Name of the analyzed project")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the project analysis",
    )
    total_files: int = Field(0, description="Total number of analyzed source files")
    total_lines_of_code: int = Field(0, description="Total physical lines of code across all files")
    overall_quality_score: int = Field(0, description="Aggregated project quality score (0-100)")
    language_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Percentage distribution of programming languages (e.g. {'python': 65.0, 'javascript': 35.0})",
    )
    security_summary: SecurityReport = Field(
        default_factory=SecurityReport,
        description="Project-wide security vulnerability summary",
    )
    files: List[FileAnalysisSummary] = Field(
        default_factory=list,
        description="Summary reports for each analyzed source file",
    )
    duplications: List[DuplicationFinding] = Field(
        default_factory=list,
        description="Detected code duplications and clone pairs across the project",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Aggregated project-wide improvement and refactoring recommendations",
    )
    execution_time_ms: float = Field(0.0, description="Total project scan execution time in ms")


class ScanHistorySummary(BaseModel):
    """Summary of a past analysis scan in local history."""

    scan_id: str
    timestamp: datetime
    target_name: str
    scan_type: str = "single_file"  # "single_file" or "project"
    language: str = "python"
    score: int = 0
    lines_of_code: int = 0
    findings_count: int = 0
    critical_security_count: int = 0
    status: str = "completed"
