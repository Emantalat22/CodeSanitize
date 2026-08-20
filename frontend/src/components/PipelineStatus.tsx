import React from 'react';
import {
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  FileCode,
  Binary,
  Cpu,
  Sparkles,
  ShieldCheck,
  FileCheck2,
} from 'lucide-react';

export type StageState = 'completed' | 'running' | 'failed' | 'pending';

export interface PipelineStageInfo {
  id: string;
  name: string;
  state: StageState;
  detail?: string;
}

interface PipelineStatusProps {
  hasCode: boolean;
  isAnalyzing: boolean;
  hasAnalyzed: boolean;
  analysisFailed: boolean;
  isTransforming: boolean;
  hasTransformed: boolean;
  transformationFailed: boolean;
  validationPassed: boolean;
}

export const PipelineStatus: React.FC<PipelineStatusProps> = ({
  hasCode,
  isAnalyzing,
  hasAnalyzed,
  analysisFailed,
  isTransforming,
  hasTransformed,
  transformationFailed,
  validationPassed,
}) => {
  const getStageState = (stageId: string): StageState => {
    switch (stageId) {
      case 'input':
        return hasCode ? 'completed' : 'pending';
      case 'parse':
        if (isAnalyzing || isTransforming) return 'running';
        if (analysisFailed || transformationFailed) return 'failed';
        if (hasAnalyzed || hasTransformed) return 'completed';
        return 'pending';
      case 'analyze':
        if (isAnalyzing) return 'running';
        if (analysisFailed) return 'failed';
        if (hasAnalyzed) return 'completed';
        return 'pending';
      case 'transform':
        if (isTransforming) return 'running';
        if (transformationFailed) return 'failed';
        if (hasTransformed) return 'completed';
        return 'pending';
      case 'validate':
        if (isTransforming) return 'running';
        if (hasTransformed && !validationPassed) return 'failed';
        if (hasTransformed && validationPassed) return 'completed';
        return 'pending';
      case 'output':
        if (hasTransformed && validationPassed) return 'completed';
        if (hasAnalyzed && !hasTransformed) return 'completed';
        return 'pending';
      default:
        return 'pending';
    }
  };

  const stages = [
    { id: 'input', name: 'Code Input', icon: FileCode, state: getStageState('input') },
    { id: 'parse', name: 'AST Parse', icon: Binary, state: getStageState('parse') },
    { id: 'analyze', name: 'Analysis', icon: Cpu, state: getStageState('analyze') },
    { id: 'transform', name: 'Safe Transform', icon: Sparkles, state: getStageState('transform') },
    { id: 'validate', name: 'Validation', icon: ShieldCheck, state: getStageState('validate') },
    { id: 'output', name: 'Output', icon: FileCheck2, state: getStageState('output') },
  ];

  return (
    <div className="pipeline-status-bar">
      <div className="pipeline-bar-header">
        <span className="pipeline-label">Execution Pipeline:</span>
      </div>

      <div className="pipeline-steps-track">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <React.Fragment key={stage.id}>
              <div className={`pipeline-track-item state-${stage.state}`}>
                <div className="track-icon-wrapper">
                  {stage.state === 'running' ? (
                    <RefreshCw size={13} className="icon-spin text-primary" />
                  ) : stage.state === 'completed' ? (
                    <CheckCircle2 size={13} className="text-success" />
                  ) : stage.state === 'failed' ? (
                    <AlertOctagon size={13} className="text-error" />
                  ) : (
                    <Icon size={13} className="text-muted" />
                  )}
                </div>
                <span className="track-name">{stage.name}</span>
                <span className={`track-state-badge badge-${stage.state}`}>
                  {stage.state === 'running'
                    ? 'RUNNING'
                    : stage.state === 'completed'
                    ? 'COMPLETED'
                    : stage.state === 'failed'
                    ? 'FAILED'
                    : 'PENDING'}
                </span>
              </div>
              {idx < stages.length - 1 && <div className="track-divider">→</div>}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
