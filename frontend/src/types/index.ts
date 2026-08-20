/**
 * Type definitions matching backend schemas and contracts for CodeSanitize.
 */

export type SupportedLanguage =
  | 'python'
  | 'javascript'
  | 'typescript'
  | 'go'
  | 'rust'
  | 'java'
  | 'cpp'
  | 'c'
  | 'csharp'
  | 'ruby'
  | 'php';

export type PipelineStatus = 'available' | 'in_development' | 'planned';

export type AnalysisStatus =
  | 'completed'
  | 'syntax_error'
  | 'parser_unavailable'
  | 'unsupported_language'
  | 'failed';

export type TransformationStatus =
  | 'completed'
  | 'partial'
  | 'no_changes_applied'
  | 'rejected'
  | 'syntax_error'
  | 'unsupported_language'
  | 'failed';

export type TransformationSafetyLevel =
  | 'safe_conservative'
  | 'safe_structural'
  | 'experimental';

export type TransformationAttemptStatus = 'accepted' | 'rejected' | 'skipped';

export type ValidationVerdict = 'passed' | 'warning' | 'failed';

export type ValidationPolicy = 'strict' | 'balanced' | 'permissive';

export type ValidationConfidenceLevel = 'high' | 'medium' | 'low' | 'unknown';

export type FindingSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export type FindingCategory =
  | 'quality'
  | 'complexity'
  | 'security'
  | 'structure'
  | 'non_functional'
  | 'similarity';

export type ValidationRiskFlag =
  | 'reflection_detected'
  | 'eval_exec_detected'
  | 'dynamic_attribute_access'
  | 'dynamic_import'
  | 'side_effect_file_io'
  | 'side_effect_subprocess'
  | 'side_effect_network'
  | 'side_effect_env'
  | 'side_effect_random_time'
  | 'side_effect_threading';

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface LanguageInfo {
  id: SupportedLanguage;
  display_name: string;
  extensions: string[];
  ast_parser: string;
  status: PipelineStatus;
}

export interface CodeInput {
  code: string;
  language: SupportedLanguage;
  filename?: string;
  options?: Record<string, unknown>;
  human_authored_mode?: boolean;
}


export interface AnalysisIssue {
  rule_id: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
  line_start?: number;
  line_end?: number;
  column_start?: number;
  column_end?: number;
  metadata?: Record<string, unknown>;
}

export interface FindingLocation {
  line_start?: number;
  line_end?: number;
  column_start?: number;
  column_end?: number;
  function_name?: string;
}

export interface AnalysisFinding {
  id: string;
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  description: string;
  location?: FindingLocation;
  evidence?: string;
  recommendation?: string;
}

export interface ComplexityFunction {
  name: string;
  complexity: number;
  risk: 'low' | 'medium' | 'high' | string;
  line_start: number;
  nesting_depth: number;
  statement_count: number;
}

export interface ComplexityFunctionMetric {
  name: string;
  line_start: number;
  cyclomatic_complexity: number;
  nesting_depth: number;
  statement_count: number;
}

export interface ComplexityReport {
  average_complexity: number;
  maximum_complexity: number;
  most_complex_functions: ComplexityFunction[];
  complexity_level: 'Low' | 'Medium' | 'High' | string;
  cyclomatic_complexity: number;
  branching_count: number;
  loop_count: number;
  max_nesting_depth: number;
  exception_handling_count: number;
  function_complexities: ComplexityFunctionMetric[];
}

export interface ComplexityMetrics {
  cyclomatic_complexity: number;
  branching_count: number;
  loop_count: number;
  max_nesting_depth: number;
  exception_handling_count: number;
  function_complexities: ComplexityFunctionMetric[];
}

export interface SecurityReport {
  critical_count: number;
  warning_count: number;
  informational_count: number;
  risk_level: 'Clean' | 'Low' | 'Medium' | 'High' | 'Critical' | string;
  findings: AnalysisFinding[];
}

export interface CodeMetrics {
  lines_of_code: number;
  blank_lines: number;
  comment_lines: number;
  function_count: number;
  class_count: number;
  import_count: number;
  average_function_length: number;
  raw_character_count?: number;
  ast_nodes_count?: number;
  variable_assignment_count?: number;
  control_flow_node_count?: number;
  max_nesting_depth?: number;
  cyclomatic_complexity?: number;
  comment_count?: number;
  docstring_count?: number;
  comment_ratio?: number;
}

export type StructuralMetrics = CodeMetrics;

export interface StructuralFingerprint {
  ast_node_hash: string;
  control_flow_fingerprint: string;
  structure_vector: number[];
  normalized_skeleton: string;
}

export interface SimilarityScore {
  score: number;
  confidence: string;
  explanation: string;
}

export interface AnalyzerReport {
  analyzer_id: string;
  analyzer_name: string;
  execution_time_ms: number;
  status: string;
  findings_count: number;
  findings: AnalysisFinding[];
}

export type ArtifactCategory = 'whitespace' | 'unicode' | 'comments' | 'formatting' | 'encoding';

export interface NonFunctionalArtifact {
  category: ArtifactCategory;
  kind: string;
  description: string;
  line_number?: number;
  column_number?: number;
  character?: string;
  unicode_code_point?: string;
  count: number;
  details: Record<string, unknown>;
}

export interface ParserCapabilities {
  ast_available: boolean;
  syntax_validation: boolean;
  metrics_collection: boolean;
  non_functional_detection: boolean;
  engine_name: string;
}

export interface AnalysisResult {
  analysis_id: string;
  language: SupportedLanguage;
  filename?: string;
  timestamp: string;
  analysis_timestamp: string;
  quality_score: number;
  overall_score: number;
  metrics: CodeMetrics;
  structural_metrics: CodeMetrics;
  complexity_report: ComplexityReport;
  complexity_metrics: ComplexityMetrics;
  security_report: SecurityReport;
  findings: AnalysisFinding[];
  recommendations: string[];
  code_length: number;
  line_count: number;
  syntax_valid: boolean;
  parser_used: string;
  analysis_status: AnalysisStatus;
  issues: AnalysisIssue[];
  fingerprint?: StructuralFingerprint;
  detected_patterns: string[];
  risk_categories: string[];
  analyzer_reports: AnalyzerReport[];
  detected_nonfunctional_artifacts: NonFunctionalArtifact[];
  capabilities: ParserCapabilities;
  execution_time_ms: number;
}

export interface TransformationRuleSpec {
  rule_id: string;
  name: string;
  description: string;
  supported_languages: SupportedLanguage[];
  safety_level: TransformationSafetyLevel;
  default_enabled: boolean;
}

export interface TransformationAttempt {
  rule_id: string;
  name: string;
  status: TransformationAttemptStatus;
  reason?: string;
  changes_description?: string;
  change_count: number;
  validation_verdict: ValidationVerdict;
  validation_message?: string;
}

export interface DiffSummary {
  additions: number;
  removals: number;
  changed_lines: number;
}

export interface ValidationDiagnostic {
  check_name: string;
  passed: boolean;
  details: string;
}

export interface ValidationCheckResult {
  check_name: string;
  passed: boolean;
  severity: ValidationVerdict;
  details: string;
  context?: Record<string, unknown>;
}

export interface ValidationTestCase {
  test_id: string;
  description: string;
  input_values: Record<string, unknown>;
  expected_output?: unknown;
  expected_exception?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  verdict: ValidationVerdict;
  confidence_level: ValidationConfidenceLevel;
  policy_applied: ValidationPolicy;
  syntax_valid: boolean;
  semantic_invariants_preserved: boolean;
  validators_run: string[];
  passed_checks: ValidationCheckResult[];
  warnings: ValidationCheckResult[];
  failures: ValidationCheckResult[];
  diagnostics: ValidationDiagnostic[];
  structural_changes: string[];
  interface_changes: string[];
  risk_flags: ValidationRiskFlag[];
  test_cases: ValidationTestCase[];
  message: string;
  timestamp: string;
}

export interface ValidateRequest {
  original_code: string;
  transformed_code: string;
  language?: SupportedLanguage;
  filename?: string;
  policy?: ValidationPolicy;
  options?: Record<string, unknown>;
}

export interface FingerprintRemediationPreview {
  fingerprint_type: string;
  detected_fingerprint: string;
  applied_fix: string;
  confidence: number;
  location?: string;
  remediation_rule: string;
}

export interface TransformationResult {
  transformation_id: string;
  language: SupportedLanguage;
  filename?: string;
  original_code: string;
  transformed_code: string;
  transformation_status: TransformationStatus;
  transformations_applied: TransformationAttempt[];
  rejected_transformations: TransformationAttempt[];
  attempt_history: TransformationAttempt[];
  change_count: number;
  diff?: string;
  diff_summary: DiffSummary;
  validation_status: ValidationVerdict;
  validation_report?: ValidationResult;
  original_ai_score?: number;
  transformed_ai_score?: number;
  reduction_percentage?: number;
  comments_removed?: number;
  identifiers_changed?: number;
  structural_patterns_changed?: number;
  redundant_logic_removed?: number;
  simplified_structures?: number;
  formatting_fixes?: number;
  remediations_applied?: FingerprintRemediationPreview[];
  removed_patterns?: string[];
  pattern_explanations?: string[];
  pattern_categories_changed?: Record<string, number>;
  remediation_passes_count?: number;
  fingerprint_rescan_report?: Record<string, any>;
  human_authored_mode?: boolean;
  warnings: string[];
  execution_time_ms: number;
  timestamp: string;

}




export interface DuplicationLocation {
  filename: string;
  line_start: number;
  line_end: number;
  function_name?: string;
}

export interface DuplicationFinding {
  id: string;
  similarity_percentage: number;
  primary_location: DuplicationLocation;
  duplicate_location: DuplicationLocation;
  duplicate_type: string;
  snippet_preview?: string;
  recommendation: string;
}

export interface ProjectFileInput {
  filename: string;
  code: string;
  language?: SupportedLanguage | string;
}

export interface ProjectAnalysisRequest {
  project_name?: string;
  files: ProjectFileInput[];
  options?: Record<string, unknown>;
}

export interface FileAnalysisSummary {
  filename: string;
  language: SupportedLanguage;
  lines_of_code: number;
  quality_score: number;
  complexity_level: string;
  security_risk: string;
  findings_count: number;
  execution_time_ms: number;
}

export interface ProjectAnalysisResult {
  project_id: string;
  project_name: string;
  timestamp: string;
  total_files: number;
  total_lines_of_code: number;
  overall_quality_score: number;
  language_distribution: Record<string, number>;
  security_summary: SecurityReport;
  files: FileAnalysisSummary[];
  duplications: DuplicationFinding[];
  recommendations: string[];
  execution_time_ms: number;
}

export interface ScanHistorySummary {
  scan_id: string;
  timestamp: string;
  target_name: string;
  scan_type: string;
  language: string;
  score: number;
  lines_of_code: number;
  findings_count: number;
  critical_security_count: number;
  status: string;
}

export interface ProvenanceSignal {
  signal_type: string;
  severity: 'low' | 'medium' | 'high';
  confidence: number;
  description: string;
  file_location?: { line_start?: number; line_end?: number };
  evidence?: string;
}

export interface CommentAnalysisResult {
  total_comments: number;
  redundant_comments_count: number;
  obvious_comments: ProvenanceSignal[];
  comment_ratio: number;
}

export interface IdentifierAnalysisResult {
  generic_identifiers_count: number;
  generic_identifiers: ProvenanceSignal[];
  repeated_naming_patterns: string[];
}

export interface StyleAnalysisResult {
  uniformity_score: number;
  excessive_regularity: boolean;
  signals: ProvenanceSignal[];
}

export interface ProvenanceReport {
  provenance_score: number;
  ai_pattern_score?: number;
  confidence_level: 'low' | 'medium' | 'high' | string;
  confidence_score?: number;
  risk_level?: 'low' | 'medium' | 'high' | string;
  signals_detected: ProvenanceSignal[];
  detected_patterns?: Record<string, unknown>[];
  ai_pattern_breakdown?: Record<string, number>;
  comment_analysis: CommentAnalysisResult;
  identifier_analysis: IdentifierAnalysisResult;
  style_analysis: StyleAnalysisResult;
  recommendations: string[];
  execution_time_ms: number;
}



