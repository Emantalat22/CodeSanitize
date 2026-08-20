# CodeSanitize

> **Safe, Semantics-Preserving Source Code Normalization, Static Code Intelligence & Multi-Stage AST Validation Engine**

CodeSanitize is a professional developer toolchain designed to analyze source code, evaluate code quality & security vulnerabilities, and execute deterministic, semantics-preserving code transformations. The system guarantees that any code transformation preserves functional equivalence, runtime contracts, and interfaces without relying on blind LLM rewrites or random text replacements.

---

## 🏗️ System Architecture

CodeSanitize is built with a decoupled, modular architecture where parsers, analyzers, transformers, and validators evolve independently.

```
Code Input (CodeInput)
   │
   ▼
Language Parser (Python AST / Tree-sitter)
   │
   ▼
Static Code Intelligence & Artifacts Pipeline (AnalyzerRegistry)
   ├── 1. Code Quality & Maintainability (CodeQualityAnalyzer)
   ├── 2. Cyclomatic Complexity & Nesting (ComplexityAnalyzer)
   ├── 3. Static Security Vulnerabilities (SecurityPatternAnalyzer)
   ├── 4. Structural AST Fingerprinting (FingerprintAnalyzer)
   ├── 5. Structural Similarity Scoring (SimilarityAnalyzer)
   └── 6. Non-Functional Artifact Scanner (NonFunctionalAnalyzer)
   │
   ▼
Deterministic Transformation Engine (One-Rule-at-a-Time)
   │
   ▼
Multi-Stage Validation Pipeline (ValidationPipeline)
   ├── 1. Syntax Integrity (SyntaxValidator)
   ├── 2. AST Structural Invariants (AstStructuralValidator)
   ├── 3. Public Interface & Signatures (PublicInterfaceValidator)
   ├── 4. Control-Flow Topology (ControlFlowValidator)
   ├── 5. Data-Flow & Lexical Scopes (DataFlowValidator)
   ├── 6. Imports & Dependencies (ImportValidator)
   ├── 7. Reflection & Eval Safeguards (ReflectionSafeguardValidator)
   ├── 8. Side-Effect Sensitivity Analysis (SideEffectValidator)
   └── 9. Static Behavioral Equivalence (StaticBehaviorValidator)
   │
   ▼
Policy Enforcement (STRICT / BALANCED / PERMISSIVE)
   │
   ▼
Unified Diff Engine & Validated Output (POST /api/transform, POST /api/analyze & POST /api/validate)
```

For full details on each pipeline stage, see [docs/architecture.md](docs/architecture.md).

---

## 📦 Project Structure

```
CodeSanitize/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (/health, /languages, /analyze, /transform, /validate)
│   │   ├── models/          # Typed Pydantic v2 schemas
│   │   ├── parsers/         # Python AST and Tree-sitter (JS, TS, Java, C++, C)
│   │   ├── analyzers/       # Quality, Complexity, Security, Fingerprint, Similarity, NonFunctional
│   │   ├── transformers/    # FormattingNormalization, AstCanonical, SafeLocalVariableRename
│   │   ├── validators/      # 9-stage ValidationPipeline & PythonTransformationValidator
│   │   ├── services/        # AnalysisService, MetricsService, TransformationEngine, DiffService
│   │   ├── config.py        # Settings & CORS config
│   │   └── main.py          # FastAPI application
│   ├── tests/               # 74 unit, integration, pipeline, and Hypothesis property-based tests
│   ├── requirements.txt     # Backend Python dependencies
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/      # CodeEditor, ActionPanel, AnalysisDashboard, AnalysisResults, TransformationResults
│   │   ├── hooks/           # useBackendHealth & state hooks
│   │   ├── services/        # API client for health, analysis, transformations, and validation
│   │   ├── types/           # TypeScript interfaces matching backend
│   │   ├── App.tsx          # Main application with Analysis and Transformation view tabs
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Modern developer dark-mode design
│   ├── package.json         # Frontend Node dependencies
│   ├── vite.config.ts       # Vite build & proxy config
│   └── README.md
│
├── docs/
│   └── architecture.md      # Detailed pipeline & safety specification
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run backend unit, integration, and property-based tests
pytest

# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Analysis Endpoint**: [http://127.0.0.1:8000/api/analyze](http://127.0.0.1:8000/api/analyze)
- **Transformations Endpoint**: [http://127.0.0.1:8000/api/transformations](http://127.0.0.1:8000/api/transformations)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup

In a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Typecheck and build verification
npm run build

# Start the Vite development server
npm run dev
```

- **Web UI**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 📊 Implementation Status

### Chunk 1: Foundation & Skeleton (Completed)
- [x] FastAPI backend application with CORS middleware.
- [x] Pydantic v2 schemas and modular contracts.
- [x] Health check monitoring and frontend status indicator.
- [x] React + TypeScript + Vite developer UI.

### Chunk 2: Real Code Analysis Foundation (Completed)
- [x] **Python AST & Tokenizer Engine**: Syntax validation, complexity, and nesting depth calculation.
- [x] **Tree-sitter Grammars**: Multi-language support for JavaScript, TypeScript, Java, C++, and C.
- [x] **Non-Functional Artifact Scanner**: Trailing whitespace, mixed indentation, excessive blank lines, invisible/special Unicode characters (`U+200B`, `U+00A0`), docstrings, and encoding declarations.

### Chunk 3: Semantics-Preserving Transformation Engine (Completed)
- [x] **POST /api/transform**: Live transformation endpoint with pre-acceptance validation.
- [x] **Formatting Normalization (`PY-FMT-NORM-01`)**: Strips trailing whitespace, collapses excessive blank line clusters, standardizes newlines.
- [x] **AST Canonical Formatting (`PY-AST-CANON-01`)**: Standardizes PEP 8 expression layout, operator spacing, and redundant parentheses.
- [x] **Safe Scope-Aware Local Variable Normalization (`PY-SAFE-LOCAL-RENAME-01`)**: Renames purely local intermediate variables within isolated function scopes while strictly preserving parameters, imports, attributes, and public APIs.
- [x] **Unified Diff Engine (`DiffService`)**: Color-coded line-by-line diff and statistical summary (+ additions, - removals).

### Chunk 4: Advanced Multi-Stage Validation & Equivalence Suite (Completed)
- [x] **POST /api/validate**: Live standalone validation endpoint returning comprehensive multi-stage diagnostic reports.
- [x] **ValidationPipeline**: Orchestration of 9 specialized validation stages.
- [x] **Syntax Integrity (`SyntaxValidator`)**: AST parsing validation.
- [x] **AST Structural Invariants (`AstStructuralValidator`)**: Verifies decorators, async/sync status, generator status (`yield`), exception blocks, and globals.
- [x] **Public Interface Invariants (`PublicInterfaceValidator`)**: Guarantees function signatures, parameters, default values, class definitions, method contracts, and `__all__` exports remain invariant.
- [x] **Control-Flow Topology Invariants (`ControlFlowValidator`)**: Tracks and verifies branching/looping structures (`if/elif/else`, `for`, `while`, `try/except/finally`, `with`, `match/case`).
- [x] **Data-Flow & Scope Safeguards (`DataFlowValidator`)**: Hierarchical lexical scope resolution, definition-use chain verification, and prevention of undefined variable loads or parameter shadowing.
- [x] **Imports & Dependencies Invariants (`ImportValidator`)**: Enforces 100% strict invariance across module imports and aliases.
- [x] **Reflection & Eval Safeguards (`ReflectionSafeguardValidator`)**: Detects `locals()`, `globals()`, `eval()`, `exec()`, `getattr()`, `setattr()`, `__dict__`, and introspection modules.
- [x] **Side-Effect Sensitivity Analysis (`SideEffectValidator`)**: Static detection of file I/O, subprocess, network, environment variables, time, and concurrency.
- [x] **Validation Policies (`STRICT`, `BALANCED`, `PERMISSIVE`)**: Configurable enforcement policies.

### Chunk 5: Real Static Code Intelligence Engine & Dashboard Integration (Completed)
- [x] **Real Static Analysis Pipeline**: Source Code → Language Detection → Parser / AST → Analyzer Registry → Analysis Modules → Quality Engine → Dashboard.
- [x] **POST /api/analyze**: Comprehensive code intelligence endpoint returning `quality_score`, `metrics`, `complexity_report`, `security_report`, and `findings`.
- [x] **Code Metrics Analyzer (`CodeMetricsAnalyzer` / `ANLZ-METRICS-01`)**: Lines of code, blank lines, comment lines, functions, classes, imports, and function lengths via AST.
- [x] **Complexity Analyzer (`ComplexityAnalyzer` / `ANLZ-CMPLX-01`)**: If statements, loops, try/except blocks, boolean conditions, nesting depth, and function complexity ranking.
- [x] **Static Security Analyzer (`SecurityAnalyzer` / `ANLZ-SEC-01`)**: Detects `eval()`, `exec()`, `subprocess` (with `shell=True`), hardcoded secret patterns, weak crypto (`md5`/`sha1`), and SQL string concatenation.
- [x] **Quality Service (`QualityService`)**: Deterministic quality scoring engine considering complexity, maintainability, security findings, and structure.

### Chunk 6: Multi-Language Parser Foundation & CIR Architecture (Completed)
- [x] **Automatic Language Detection (`LanguageDetector`)**: Tiered detection via file extension, shebang header lines, and token syntax heuristics.
- [x] **Common Intermediate Representation (`CIRExtractor` / `IRProgram`)**: Unified, language-agnostic AST representation capturing functions, classes/structs, imports, control flow, assignments, calls, and comments.
- [x] **Multi-Language Support Foundation**: Python, JavaScript, TypeScript, Java, C++, C, Go, Rust, Ruby, PHP, and C#.
- [x] **Multi-Language Security Pattern Scanner**: Cross-language detection of dangerous dynamic execution, shell injection, secrets, and SQL concatenations.

### Chunk 7: Production Hardening & Developer Platform Features (Completed)
- [x] **Multi-File Project Analysis (`ProjectAnalysisService`)**: Scan entire codebases or uploaded ZIP archives with aggregate metrics, LOC, language distribution, and overall quality scoring.
- [x] **Code Duplication & Clone Detection (`DuplicationDetector`)**: Identifies identical and near-identical functions, repeated code blocks, and structural clones with line boundaries and similarity percentages.
- [x] **Intelligent Recommendation Engine (`RecommendationService`)**: Synthesizes prioritized refactoring hotspots, security remediations, and DRY suggestions.
- [x] **Multi-Format Report Export (`ReportService`)**: Export comprehensive analysis summaries in JSON, standalone print-ready HTML, and PDF formats.
- [x] **Local History Persistence (`HistoryService`)**: Local persistence of single-file and project scans with scan listing, retrieval, and deletion APIs.
- [x] **113 / 113 Pytest Tests Passed in 3.15s**.




---

## ⚠️ Current Scope & Limitations

- **Conservative Scope**: Currently, deep AST intelligence, transformations, and validation operate on Python source code, with multi-language parsing supported via Tree-sitter.
- **No Watermark or Authorship Claims**: CodeSanitize does not claim to detect or defeat AI watermarks or identify author provenance. All analysis is purely structural and static.
- **Formal Proof**: Automated pre-acceptance validation verifies structural, syntactic, interface, control-flow, and data-flow invariants; it does not constitute a formal mathematical proof of total runtime semantic equivalence.
