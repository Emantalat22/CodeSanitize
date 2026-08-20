import React from 'react';
import { Shield, GitBranch, CheckSquare, Layers } from 'lucide-react';

export const StatusBanner: React.FC = () => {
  return (
    <div className="pillars-grid">
      <div className="pillar-card">
        <div className="pillar-icon-wrapper">
          <Shield size={20} className="text-primary" />
        </div>
        <div className="pillar-content">
          <h3>Semantics-Preserving</h3>
          <p>
            Transforms AST nodes with formal equivalence verification to ensure the original
            program runtime behavior and functionality remain strictly invariant.
          </p>
        </div>
      </div>

      <div className="pillar-card">
        <div className="pillar-icon-wrapper">
          <Layers size={20} className="text-accent" />
        </div>
        <div className="pillar-content">
          <h3>Modular Architecture</h3>
          <p>
            Language parsers, static analyzers, AST transformers, and validation suites are
            decoupled as modular, independent subsystems.
          </p>
        </div>
      </div>

      <div className="pillar-card">
        <div className="pillar-icon-wrapper">
          <GitBranch size={20} className="text-warning" />
        </div>
        <div className="pillar-content">
          <h3>Deterministic AST Rules</h3>
          <p>
            Zero random text replacements and zero blind LLM hallucinations. Transformations
            follow rigorous, deterministic compiler-level rules.
          </p>
        </div>
      </div>

      <div className="pillar-card">
        <div className="pillar-icon-wrapper">
          <CheckSquare size={20} className="text-success" />
        </div>
        <div className="pillar-content">
          <h3>Pre-acceptance Validation</h3>
          <p>
            Every transformation must pass automated syntax, AST diff, and semantic equivalence
            validation checks before being presented or exported.
          </p>
        </div>
      </div>
    </div>
  );
};
