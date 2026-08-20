import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  AnalysisResult,
  SupportedLanguage,
  TransformationResult,
  ValidationPolicy,
  ProvenanceReport,
} from '../types';
import { analyzeCode, transformCode, analyzeProvenance } from '../services/api';
import { useBackendHealth, BackendHealthState } from '../hooks/useBackendHealth';

const DEFAULT_PYTHON_RULES = [
  'PY-FMT-NORM-01',
  'PY-AST-CANON-01',
  'PY-SAFE-LOCAL-RENAME-01',
  'PY-STRUCT-SIMPLIFY-01',
  'PROV-COMMENT-NORM-01',
  'PROV-STYLE-NORM-01',
  'AI-PATTERN-NORM-01',
];


const INITIAL_CODE = `# Import required modules
import math

# Function to compute geometric properties
def calculate_circle_metrics(radius: float) -> dict:
    # Initialize empty result dictionary
    result_data = {}
    
    # Calculate area and perimeter
    temp_area = math.pi * (radius ** 2)
    temp_circumference = 2 * math.pi * radius
    
    result_data["area"] = temp_area
    result_data["circumference"] = temp_circumference
    
    # Return the result
    return result_data

if __name__ == '__main__':
    print("Testing output:", calculate_circle_metrics(5.0))
`;

interface WorkspaceContextType {
  code: string;
  setCode: (code: string) => void;
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  filename: string;
  setFilename: (name: string) => void;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  analysisError: string | null;
  runAnalysis: () => Promise<void>;
  transformationResult: TransformationResult | null;
  isTransforming: boolean;
  transformError: string | null;
  runTransform: () => Promise<void>;
  enabledRules: string[];
  toggleRule: (ruleId: string) => void;
  validationPolicy: ValidationPolicy;
  setValidationPolicy: (policy: ValidationPolicy) => void;
  provenanceReport: ProvenanceReport | null;
  isAnalyzingProvenance: boolean;
  runProvenance: () => Promise<void>;
  applyTransformedCode: (newCode: string) => Promise<void>;
  backendHealth: BackendHealthState;
}


const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [code, setCode] = useState<string>(INITIAL_CODE);
  const [language, setLanguage] = useState<SupportedLanguage>('python');
  const [filename, setFilename] = useState<string>('main.py');

  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [transformationResult, setTransformationResult] = useState<TransformationResult | null>(null);
  const [isTransforming, setIsTransforming] = useState<boolean>(false);
  const [transformError, setTransformError] = useState<string | null>(null);
  const [enabledRules, setEnabledRules] = useState<string[]>(DEFAULT_PYTHON_RULES);
  const [validationPolicy, setValidationPolicy] = useState<ValidationPolicy>('strict');

  const [provenanceReport, setProvenanceReport] = useState<ProvenanceReport | null>(null);
  const [isAnalyzingProvenance, setIsAnalyzingProvenance] = useState<boolean>(false);

  const backendHealth = useBackendHealth(8000);

  const runAnalysis = async () => {
    if (!code.trim()) return;
    setIsAnalyzing(true);
    setIsAnalyzingProvenance(true);
    setAnalysisError(null);

    try {
      const [resAnalysis, resProvenance] = await Promise.all([
        analyzeCode({
          code,
          language,
          filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
        }),
        analyzeProvenance({
          code,
          language,
          filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
        }),
      ]);
      setAnalysisResult(resAnalysis);
      setProvenanceReport(resProvenance);
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
      setIsAnalyzingProvenance(false);
    }
  };

  const runTransform = async () => {
    if (!code.trim() || isTransforming) return;
    setIsTransforming(true);
    setTransformError(null);

    try {
      const result = await transformCode({
        code,
        language,
        filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
        options: {
          enabled_transformations: enabledRules,
          validation_policy: validationPolicy,
        },
      });
      setTransformationResult(result);
    } catch (err) {
      setTransformError(err instanceof Error ? err.message : 'Transformation failed');
    } finally {
      setIsTransforming(false);
    }
  };

  const runProvenance = async () => {
    if (!code.trim() || isAnalyzingProvenance) return;
    setIsAnalyzingProvenance(true);

    try {
      const res = await analyzeProvenance({
        code,
        language,
        filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
      });
      setProvenanceReport(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzingProvenance(false);
    }
  };

  const applyTransformedCode = async (newCode: string) => {
    setCode(newCode);
    setTransformationResult(null);
    setIsAnalyzing(true);
    setIsAnalyzingProvenance(true);
    try {
      const [resAnalysis, resProvenance] = await Promise.all([
        analyzeCode({
          code: newCode,
          language,
          filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
        }),
        analyzeProvenance({
          code: newCode,
          language,
          filename: filename || `main.${language === 'python' ? 'py' : 'txt'}`,
        }),
      ]);
      setAnalysisResult(resAnalysis);
      setProvenanceReport(resProvenance);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
      setIsAnalyzingProvenance(false);
    }
  };

  const toggleRule = (ruleId: string) => {
    setEnabledRules((prev) =>
      prev.includes(ruleId) ? prev.filter((r) => r !== ruleId) : [...prev, ruleId]
    );
  };


  // Run initial analysis automatically once connected
  useEffect(() => {
    if (backendHealth.status === 'connected' && !analysisResult && code) {
      runAnalysis();
    }
  }, [backendHealth.status]);

  return (
    <WorkspaceContext.Provider
      value={{
        code,
        setCode,
        language,
        setLanguage,
        filename,
        setFilename,
        analysisResult,
        isAnalyzing,
        analysisError,
        runAnalysis,
        transformationResult,
        isTransforming,
        transformError,
        runTransform,
        enabledRules,
        toggleRule,
        validationPolicy,
        setValidationPolicy,
        provenanceReport,
        isAnalyzingProvenance,
        runProvenance,
        applyTransformedCode,
        backendHealth,
      }}

    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = (): WorkspaceContextType => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
