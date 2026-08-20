import {
  AnalysisResult,
  CodeInput,
  HealthResponse,
  LanguageInfo,
  SupportedLanguage,
  TransformationResult,
  TransformationRuleSpec,
  ValidateRequest,
  ValidationResult,
  ProvenanceReport,
} from '../types';


const envBaseUrl: string =
  (import.meta.env?.VITE_API_BASE_URL as string | undefined) ||
  (import.meta.env?.VITE_API_URL as string | undefined) ||
  '/api';
const API_BASE_URL = envBaseUrl.endsWith('/') ? envBaseUrl.slice(0, -1) : envBaseUrl;

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Perform a GET /api/health check and measure response time.
 */
export async function getHealthStatus(): Promise<{
  data: HealthResponse;
  latencyMs: number;
}> {
  const startTime = performance.now();
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      throw new ApiError(
        `Health check failed with status ${response.status}`,
        response.status
      );
    }

    const data: HealthResponse = await response.json();
    return { data, latencyMs };
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Network error communicating with backend'
    );
  }
}

/**
 * Retrieve supported languages and parser status from backend.
 */
export async function getSupportedLanguages(): Promise<LanguageInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/languages`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new ApiError(
        `Failed to fetch languages: HTTP ${response.status}`,
        response.status
      );
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Failed to fetch languages'
    );
  }
}

/**
 * Request real backend source code analysis via POST /api/analyze.
 */
export async function analyzeCode(input: CodeInput): Promise<AnalysisResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      let errorDetail = `Analysis failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // use default errorDetail
      }
      throw new ApiError(errorDetail, response.status);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Failed to connect to analysis engine'
    );
  }
}

/**
 * List available semantics-preserving transformation rules.
 */
export async function getTransformationRules(
  language?: SupportedLanguage
): Promise<TransformationRuleSpec[]> {
  try {
    const url = language
      ? `${API_BASE_URL}/transformations?language=${language}`
      : `${API_BASE_URL}/transformations`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new ApiError(`Failed to fetch rules: HTTP ${response.status}`, response.status);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err instanceof Error ? err.message : 'Failed to fetch transformation rules');
  }
}

/**
 * Request semantics-preserving transformation via POST /api/transform.
 */
export async function transformCode(input: CodeInput): Promise<TransformationResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/transform`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      let errorDetail = `Transformation failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // use default errorDetail
      }
      throw new ApiError(errorDetail, response.status);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Failed to connect to transformation engine'
    );
  }
}

/**
 * Request standalone multi-stage validation via POST /api/validate.
 */
export async function validateCode(request: ValidateRequest): Promise<ValidationResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorDetail = `Validation failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // use default errorDetail
      }
      throw new ApiError(errorDetail, response.status);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Failed to connect to validation pipeline'
    );
  }
}

/**
 * Request multi-file project analysis via POST /api/project/analyze.
 */
export async function analyzeProject(request: {
  project_name?: string;
  files: Array<{ filename: string; code: string; language?: string }>;
  options?: Record<string, unknown>;
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/project/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ApiError(`Project analysis failed with HTTP ${response.status}`, response.status);
    }
    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err instanceof Error ? err.message : 'Failed to analyze project');
  }
}

/**
 * Upload and analyze project ZIP archive via POST /api/project/upload.
 */
export async function uploadProjectZip(file: File, projectName?: string) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const url = projectName
      ? `${API_BASE_URL}/project/upload?project_name=${encodeURIComponent(projectName)}`
      : `${API_BASE_URL}/project/upload`;

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(`ZIP upload analysis failed with HTTP ${response.status}`, response.status);
    }
    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err instanceof Error ? err.message : 'Failed to upload project ZIP');
  }
}

/**
 * Request AI code provenance and synthetic pattern analysis via POST /api/provenance.
 */
export async function analyzeProvenance(input: CodeInput): Promise<ProvenanceReport> {
  try {
    let response = await fetch(`${API_BASE_URL}/provenance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(input),
    });

    if (response.status === 404) {
      // Fallback to /api/provenance/analyze
      response = await fetch(`${API_BASE_URL}/provenance/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(input),
      });
    }

    if (!response.ok) {
      throw new ApiError(`Provenance analysis failed with HTTP ${response.status}`, response.status);
    }
    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err instanceof Error ? err.message : 'Failed to analyze code provenance');
  }
}



