import React from 'react';
import { Terminal, BookOpen, GitFork } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-left">
          <div className="footer-badge">
            <Terminal size={14} />
            <span>CodeSanitize Developer Toolchain</span>
          </div>
          <span className="footer-copyright">
            Safe Code Normalization & Transformation Engine &bull; Modular AST Architecture
          </span>
        </div>
        <div className="footer-right">
          <div className="footer-links">
            <span className="footer-link">
              <BookOpen size={14} />
              <span>docs/architecture.md</span>
            </span>
            <span className="footer-link">
              <GitFork size={14} />
              <span>Pipeline: Chunk 1 Foundation</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
