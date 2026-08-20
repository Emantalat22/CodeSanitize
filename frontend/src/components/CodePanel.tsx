import React, { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';


interface CodePanelProps {
  title: string;
  code: string;
  language?: string;
  filename?: string;
  badge?: {
    text: string;
    variant: 'before' | 'after' | 'info';
  };
  readOnly?: boolean;
  onChange?: (code: string) => void;
  height?: string | number;
  highlightLines?: number[];
  onScroll?: () => void;
  scrollRef?: React.RefObject<HTMLDivElement>;
}

export const CodePanel: React.FC<CodePanelProps> = ({
  title,
  code,
  language = 'python',
  filename,
  badge,
  readOnly = true,
  onChange,
  height,
  scrollRef,
  onScroll,
}) => {
  const [copied, setCopied] = useState(false);
  const lines = code.split('\n');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `code.${language === 'python' ? 'py' : 'txt'}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="code-panel-pro" style={{ height: height || '100%' }}>
      <div className="code-panel-header">
        <div className="panel-header-left">
          {badge && (
            <span className={`panel-badge badge-${badge.variant}`}>
              {badge.text}
            </span>
          )}
          <span className="panel-title-text">{title}</span>
          {filename && <span className="panel-filename-tag">{filename}</span>}
        </div>

        <div className="panel-header-right">
          <span className="lines-count-tag">{lines.length} lines</span>
          <button
            type="button"
            onClick={handleCopy}
            className="panel-icon-btn"
            title="Copy code to clipboard"
          >
            {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="panel-icon-btn"
            title="Download file"
          >
            <Download size={13} />
          </button>
        </div>
      </div>

      <div className="code-panel-body" ref={scrollRef} onScroll={onScroll}>
        <div className="code-gutter-pro">
          {lines.map((_, i) => (
            <div key={i + 1} className="gutter-num">
              {i + 1}
            </div>
          ))}
        </div>

        {readOnly ? (
          <pre className="code-pre-pro">{code}</pre>
        ) : (
          <textarea
            className="code-textarea-pro"
            value={code}
            onChange={(e) => onChange && onChange(e.target.value)}
            spellCheck={false}
          />
        )}
      </div>
    </div>
  );
};
