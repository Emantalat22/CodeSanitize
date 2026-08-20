import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { SupportedLanguage } from '../types';
import {
  FileCode,
  Copy,
  Check,
  Trash2,
  Binary,
  Code2,
  FolderOpen,
} from 'lucide-react';

interface CodeEditorProps {
  code: string;
  onChange: (code: string) => void;
  language: SupportedLanguage;
  onLanguageChange: (lang: SupportedLanguage) => void;
  filename?: string;
  onFilenameChange?: (name: string) => void;
  height?: string;
}

const SAMPLE_SNIPPETS: Record<SupportedLanguage, string> = {
  python: `import os
import math

def process_coordinates(points: list[tuple[float, float]]) -> dict:
    """Calculate bounding box and centroid of 2D coordinates."""
    if not points:
        return {"centroid": (0.0, 0.0), "area": 0.0}

    sum_x = 0.0
    sum_y = 0.0
    min_x = points[0][0]
    max_x = points[0][0]

    for pt_x, pt_y in points:
        sum_x += pt_x
        sum_y += pt_y
        if pt_x < min_x:
            min_x = pt_x
        if pt_x > max_x:
            max_x = pt_x

    count = len(points)
    centroid = (round(sum_x / count, 2), round(sum_y / count, 2))
    span_width = max_x - min_x

    return {
        "count": count,
        "centroid": centroid,
        "span_width": span_width,
    }

if __name__ == "__main__":
    coords = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
    stats = process_coordinates(coords)
    print("Computed Stats:", stats)
`,
  javascript: `function processCoordinates(points) {
  // Calculate centroid and bounding width
  if (!points || points.length === 0) {
    return { centroid: [0, 0], count: 0 };
  }

  let sumX = 0;
  let sumY = 0;
  for (let i = 0; i < points.length; i++) {
    sumX += points[i][0];
    sumY += points[i][1];
  }

  const count = points.length;
  return {
    count,
    centroid: [Number((sumX / count).toFixed(2)), Number((sumY / count).toFixed(2))]
  };
}

const coords = [[1, 2], [3, 4], [5, 6]];
console.log(processCoordinates(coords));
`,
  typescript: `interface CoordinateResult {
  count: number;
  centroid: [number, number];
}

export function processCoordinates(points: [number, number][]): CoordinateResult {
  if (points.length === 0) {
    return { count: 0, centroid: [0, 0] };
  }

  let sumX = 0;
  let sumY = 0;
  for (const [x, y] of points) {
    sumX += x;
    sumY += y;
  }

  const count = points.length;
  return {
    count,
    centroid: [Number((sumX / count).toFixed(2)), Number((sumY / count).toFixed(2))]
  };
}
`,
  java: `import java.util.List;

public class CoordinatesProcessor {
    public static class Result {
        public int count;
        public double avgX;
        public double avgY;

        public Result(int count, double avgX, double avgY) {
            this.count = count;
            this.avgX = avgX;
            this.avgY = avgY;
        }
    }

    public static Result process(List<double[]> points) {
        if (points == null || points.isEmpty()) {
            return new Result(0, 0.0, 0.0);
        }
        double sumX = 0;
        double sumY = 0;
        for (double[] pt : points) {
            sumX += pt[0];
            sumY += pt[1];
        }
        int count = points.size();
        return new Result(count, sumX / count, sumY / count);
    }
}
`,
  cpp: `#include <iostream>
#include <vector>

struct Point {
    double x;
    double y;
};

struct Stats {
    size_t count;
    double avg_x;
    double avg_y;
};

Stats compute_stats(const std::vector<Point>& points) {
    if (points.empty()) return {0, 0.0, 0.0};
    double sum_x = 0.0, sum_y = 0.0;
    for (const auto& p : points) {
        sum_x += p.x;
        sum_y += p.y;
    }
    return {points.size(), sum_x / points.size(), sum_y / points.size()};
}
`,
  c: `#include <stdio.h>

struct Point {
    double x;
    double y;
};

double calculate_sum_x(struct Point* pts, int len) {
    double s = 0;
    for (int i = 0; i < len; i++) {
        s += pts[i].x;
    }
    return s;
}
`,
  go: `package main

import "fmt"

type Point struct {
	X float64
	Y float64
}

func ProcessPoints(points []Point) (float64, float64) {
	if len(points) == 0 {
		return 0, 0
	}
	var sumX, sumY float64
	for _, p := range points {
		sumX += p.X
		sumY += p.Y
	}
	count := float64(len(points))
	return sumX / count, sumY / count
}

func main() {
	pts := []Point{{1, 2}, {3, 4}}
	avgX, avgY := ProcessPoints(pts)
	fmt.Printf("Avg: %.2f, %.2f\\n", avgX, avgY)
}
`,
  rust: `pub struct Point {
    pub x: f64,
    pub y: f64,
}

pub fn average_coordinates(points: &[Point]) -> (f64, f64) {
    if points.is_empty() {
        return (0.0, 0.0);
    }
    let (sum_x, sum_y) = points.iter().fold((0.0, 0.0), |(sx, sy), p| {
        (sx + p.x, sy + p.y)
    });
    let count = points.len() as f64;
    (sum_x / count, sum_y / count)
}
`,
  csharp: `using System;
using System.Collections.Generic;

public class CoordinateAnalyzer {
    public static (double avgX, double avgY) CalculateCenter(List<(double X, double Y)> points) {
        if (points == null || points.Count == 0) return (0.0, 0.0);
        double sumX = 0, sumY = 0;
        foreach (var p in points) {
            sumX += p.X;
            sumY += p.Y;
        }
        return (sumX / points.Count, sumY / points.Count);
    }
}
`,
  ruby: `def calculate_center(points)
  return [0.0, 0.0] if points.nil? || points.empty?
  sum_x = points.sum { |p| p[0] }
  sum_y = points.sum { |p| p[1] }
  count = points.length.to_f
  [sum_x / count, sum_y / count]
end
`,
  php: `<?php

function calculateCoordinates(array $points): array {
    if (empty($points)) {
        return ['count' => 0, 'avg_x' => 0.0, 'avg_y' => 0.0];
    }
    $sumX = 0.0;
    $sumY = 0.0;
    foreach ($points as $pt) {
        $sumX += $pt[0];
        $sumY += $pt[1];
    }
    $count = count($points);
    return [
        'count' => $count,
        'avg_x' => $sumX / $count,
        'avg_y' => $sumY / $count
    ];
}
`,
};

const EXTENSION_MAP: Record<SupportedLanguage, string> = {
  python: 'main.py',
  javascript: 'index.js',
  typescript: 'index.ts',
  java: 'Main.java',
  cpp: 'main.cpp',
  c: 'main.c',
  go: 'main.go',
  rust: 'main.rs',
  csharp: 'Program.cs',
  ruby: 'main.rb',
  php: 'index.php',
};

const MONACO_LANG_MAP: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  java: 'java',
  cpp: 'cpp',
  c: 'c',
  go: 'go',
  rust: 'rust',
  csharp: 'csharp',
  ruby: 'ruby',
  php: 'php',
  auto: 'python',
};

const LANGUAGES: { id: SupportedLanguage; name: string }[] = [
  { id: 'python', name: 'Python (.py)' },
  { id: 'javascript', name: 'JavaScript (.js)' },
  { id: 'typescript', name: 'TypeScript (.ts)' },
  { id: 'java', name: 'Java (.java)' },
  { id: 'cpp', name: 'C++ (.cpp)' },
  { id: 'c', name: 'C (.c)' },
  { id: 'go', name: 'Go (.go)' },
  { id: 'rust', name: 'Rust (.rs)' },
  { id: 'csharp', name: 'C# (.cs)' },
  { id: 'ruby', name: 'Ruby (.rb)' },
  { id: 'php', name: 'PHP (.php)' },
];

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  onChange,
  language,
  onLanguageChange,
  filename,
  onFilenameChange,
  height = '620px',
}) => {
  const [copied, setCopied] = useState(false);

  const lines = code ? code.split('\n') : [''];
  const lineCount = lines.length;
  const charCount = code ? code.length : 0;
  const byteSize = new Blob([code || '']).size;
  const formattedSize = byteSize < 1024 ? `${byteSize} B` : `${(byteSize / 1024).toFixed(1)} KB`;

  const activeFilename = filename || EXTENSION_MAP[language] || 'main.py';
  const monacoLanguage = MONACO_LANG_MAP[language] || 'python';

  const handleCopy = async () => {
    if (!code) return;
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadSample = () => {
    onChange(SAMPLE_SNIPPETS[language] || SAMPLE_SNIPPETS.python);
  };

  return (
    <div className="editor-card">
      {/* IDE-Style Header */}
      <div className="editor-toolbar">
        {/* Left Side: Active File & Language Selector */}
        <div className="toolbar-left">
          <div className="file-indicator">
            <FolderOpen size={14} className="text-primary" />
            <input
              type="text"
              value={activeFilename}
              onChange={(e) => onFilenameChange && onFilenameChange(e.target.value)}
              className="filename-input"
              title="Virtual source filename"
              aria-label="Filename"
            />
          </div>

          <span className="toolbar-divider"></span>

          <div className="lang-select-group">
            <label htmlFor="language-select" className="toolbar-label">
              <Code2 size={14} className="text-muted" />
              <span>Language:</span>
            </label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => onLanguageChange(e.target.value as SupportedLanguage)}
              className="lang-select"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <span className="toolbar-divider"></span>

          <button
            type="button"
            onClick={loadSample}
            className="toolbar-btn"
            title="Load sample code for selected language"
          >
            <FileCode size={13} />
            <span>Load Sample</span>
          </button>
        </div>

        {/* Right Side: Metrics Pills & Action Buttons */}
        <div className="toolbar-right">
          <span className="status-tag ast-ready" title="AST parser available for this grammar">
            <Binary size={12} />
            <span>AST READY</span>
          </span>

          <span className="stats-pill" title="Physical line count">
            {lineCount} {lineCount === 1 ? 'Line' : 'Lines'}
          </span>

          <span className="stats-pill" title="Character count">
            {charCount} Chars
          </span>

          <span className="stats-pill" title="Raw file payload size">
            {formattedSize}
          </span>

          <span className="toolbar-divider"></span>

          <button
            type="button"
            onClick={handleCopy}
            disabled={!code}
            className="toolbar-btn"
            title="Copy code to clipboard (Ctrl+C)"
          >
            {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            type="button"
            onClick={() => onChange('')}
            disabled={!code}
            className="toolbar-btn btn-danger-hover"
            title="Clear editor content"
          >
            <Trash2 size={13} />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="monaco-editor-wrapper">
        <Editor
          height={height}
          width="100%"
          language={monacoLanguage}
          value={code}
          onChange={(value) => onChange(value || '')}
          theme="vs-dark"
          loading={
            <div className="monaco-loading-state">
              <Code2 size={24} className="icon-spin text-teal" />
              <span>Initializing Monaco Editor...</span>
            </div>
          }
          options={{
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            fontSize: 14,
            lineHeight: 22,
            wordWrap: 'on',
            automaticLayout: true,
            scrollBeyondLastLine: false,
            tabSize: 4,
            lineNumbers: 'on',
            lineNumbersMinChars: 3,
            glyphMargin: false,
            folding: true,
            foldingHighlight: true,
            showFoldingControls: 'always',
            minimap: { enabled: true, maxColumn: 80, scale: 1 },
            matchBrackets: 'always',
            bracketPairColorization: { enabled: true },
            autoIndent: 'full',
            formatOnPaste: true,
            formatOnType: true,
            quickSuggestions: {
              other: true,
              comments: false,
              strings: true,
            },
            suggestOnTriggerCharacters: true,
            acceptSuggestionOnEnter: 'on',
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            renderLineHighlight: 'all',
            renderWhitespace: 'selection',
            padding: { top: 14, bottom: 14 },
            overviewRulerBorder: false,
            scrollbar: {
              vertical: 'visible',
              horizontal: 'visible',
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
              useShadows: false,
            },
          }}
        />
      </div>
    </div>
  );
};
