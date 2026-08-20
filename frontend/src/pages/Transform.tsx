import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

import { useWorkspace } from '../context/WorkspaceContext';
import { TransformationResults } from '../components/TransformationResults';
import { EmptyState } from '../components/EmptyState';

export const Transform: React.FC = () => {
  const navigate = useNavigate();
  const {
    code,
    transformationResult,
    isTransforming,
    runTransform,
    applyTransformedCode,
  } = useWorkspace();

  // Auto-run transform if no result yet exists and code is present
  useEffect(() => {
    if (!transformationResult && !isTransforming && code.trim()) {
      runTransform();
    }
  }, []);

  const handleApplyToEditor = async (newCode: string) => {
    await applyTransformedCode(newCode);
    navigate('/analyze');
  };


  return (
    <div className="page-transform-layout">
      {transformationResult ? (
        <TransformationResults
          result={transformationResult}
          onReTransform={runTransform}
          isTransforming={isTransforming}
          onApplyToEditor={handleApplyToEditor}
        />
      ) : isTransforming ? (
        <div className="transform-loading-container">
          <Sparkles size={40} className="text-purple icon-spin" />
          <h3>Executing Safe Normalization Pipeline...</h3>
          <p>
            Applying formatting normalization, AST canonicalization, and safe local variable renaming with 9-stage multi-stage invariant validation.
          </p>
        </div>
      ) : (
        <EmptyState
          icon={<Sparkles size={36} className="text-purple" />}
          title="Safe Semantics-Preserving Transformation"
          description="Execute conservative AST normalization, stripping redundant synthetic comments and standardizing formatting with strict equivalence guarantees."
          actionText="Run Safe Transformation"
          actionIcon={<Sparkles size={14} />}
          onAction={runTransform}
        />
      )}
    </div>
  );
};
