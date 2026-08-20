import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Activity } from 'lucide-react';

import { useWorkspace } from '../context/WorkspaceContext';
import { ProvenanceDashboard } from '../components/ProvenanceDashboard';
import { EmptyState } from '../components/EmptyState';

export const Provenance: React.FC = () => {
  const navigate = useNavigate();
  const {
    code,
    provenanceReport,
    isAnalyzingProvenance,
    runProvenance,
    runTransform,
    isTransforming,
  } = useWorkspace();

  // Auto-run provenance analysis if not yet loaded
  useEffect(() => {
    if (!provenanceReport && !isAnalyzingProvenance && code.trim()) {
      runProvenance();
    }
  }, []);

  const handleRemoveAIFingerprint = async () => {
    navigate('/transform');
    await runTransform();
  };

  return (
    <div className="page-provenance-layout">
      {provenanceReport ? (
        <ProvenanceDashboard
          report={provenanceReport}
          onNavigateToTransform={() => navigate('/transform')}
          onRemoveAIFingerprint={handleRemoveAIFingerprint}
          isTransforming={isTransforming}
        />
      ) : isAnalyzingProvenance ? (

        <div className="transform-loading-container">
          <Bot size={40} className="text-teal icon-spin" />
          <h3>Inspecting Code Provenance Characteristics...</h3>
          <p>
            Analyzing comment patterns, formulaic identifier naming structures, and formatting symmetry using deterministic static inspection.
          </p>
        </div>
      ) : (
        <EmptyState
          icon={<Bot size={36} className="text-teal" />}
          title="AI Code Provenance Pattern Inspection"
          description="Identify synthetic/generated code traits like redundant explanatory comments, generic identifiers, and structural regularities."
          actionText="Run Provenance Inspection"
          actionIcon={<Activity size={14} />}
          onAction={runProvenance}
        />
      )}
    </div>
  );
};
