# CodeSanitize - System Architecture & Pipeline Specification

## 1. Overview & Core Philosophy

**CodeSanitize** is a professional developer platform designed for deterministic, semantics-preserving source code normalization, static analysis intelligence, and multi-file codebase auditing.

### Core Architectural Principles:
1. **Semantics-First Guarantee**: Every transformation MUST strictly preserve the runtime behavior, computational complexity class, variable scoping, and side-effects of the original code.
2. **No Blind LLM Rewrites**: Transformations and analysis are executed via deterministic compiler AST passes and static pattern rules, not probabilistic neural network generation.
3. **No Random Text Replacements**: Zero regex-based ad-hoc token substitutions that can violate syntactic or semantic correctness.
4. **Mandatory Pre-Acceptance Validation**: Transformed code is never accepted or output unless it passes multi-stage automated equivalence and syntax validation.
5. **Decoupled Modular Architecture**: Parsers, Analyzers, Transformers, and Validators evolve independently across programming languages.
6. **No Arbitrary Code Execution**: CodeSanitize **never** executes arbitrary user-submitted code using `eval()`, `exec()`, or host subprocesses during analysis, validation, or transformation.
7. **No Fake Provenance / Watermark Claims**: Non-functional character, formatting traits, and structural fingerprints are categorized strictly as structural artifacts without unsubstantiated AI watermark or authorship claims.

---

## 2. Complete Pipeline Architecture

```
Source Code (Single File or Multi-File Project / ZIP Archive)
    ↓
Language Detection (Extension / Shebang / Syntax Heuristics)
    ↓
Parser Registry & Common Intermediate Representation (CIR)
    ↓
Analyzer Registry
    ├── Code Metrics Analyzer (LOC, Functions, Classes, Imports)
    ├── Complexity Analyzer (McCabe, Loops, Branches, Nesting)
    ├── Security Static Analyzer (eval/exec, shell=True, secrets, crypto)
    ├── Duplication & Clone Detector (Functions, Recurring Blocks)
    └── Structural Fingerprint & Similarity Analyzer
    ↓
Quality Engine & Recommendation Synthesizer
    ↓
Analysis Result & Local History Persistence
    ↓
Report Generation (JSON, Print-Ready HTML, PDF) & Frontend Dashboard
```

---

## 3. Real Static Code Intelligence Layer (Chunk 5)

The `AnalyzerRegistry` coordinates modular, read-only static analysis engines that evaluate code metrics, cyclomatic complexity, security vulnerabilities, and quality scores without executing user code.

### Modular Analyzers:

1. **Code Metrics Analyzer (`CodeMetricsAnalyzer` / `ANLZ-METRICS-01`)**:
   - Calculates physical lines of code, blank lines, single/multi-line comment lines.
   - Measures AST function counts, class declarations, import statements, and average function length.
   - Computes documentation ratio and identifies oversized functions.

2. **Complexity Analyzer (`ComplexityAnalyzer` / `ANLZ-CMPLX-01`)**:
   - Computes McCabe cyclomatic complexity per function and across the entire module.
   - Tracks branching statements (`if`/`elif`), loops (`for`/`while`/`async for`), boolean conditions (`and`/`or`), and exception handlers (`try`/`except`).
   - Produces function complexity rankings with categorized risk tiers (`Low`, `Medium`, `High`) and nesting depth warnings.

3. **Security Static Analyzer (`SecurityAnalyzer` / `ANLZ-SEC-01`)**:
   - Purely static pattern detection across languages without execution:
     - Dynamic code execution: `eval()`, `exec()`
     - Insecure subprocess invocation: `subprocess.run(..., shell=True)`, `os.system()`, `Runtime.getRuntime().exec`
     - Hardcoded API credentials, tokens, and plaintext passwords
     - Dangerous imports: `telnetlib`, `pickle`, `shelve`
     - Weak cryptographic hashes: `hashlib.md5()`, `hashlib.sha1()`
     - Suspicious SQL string concatenations
   - Categorizes findings by severity (`Critical`, `High`, `Medium`, `Low`, `Info`).

4. **Quality Scoring Engine (`QualityService`)**:
   - Generates deterministic, static-analysis-grade code quality scores ($0–100$).
   - Evaluates complexity debt, documentation coverage, nesting penalties, and security finding severities.

---

## 4. Multi-Language Parser Foundation & Architecture (Chunk 6)

### Language Detection Engine (`LanguageDetector`):
- **Tier 1: Extension Mapping**: Maps file extensions (`.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.rb`, `.php`, `.cs`) to `SupportedLanguage`.
- **Tier 2: Shebang Inspection**: Inspects `#!` header lines (`#!/usr/bin/env python3`, `#!/usr/bin/env node`, etc.).
- **Tier 3: Syntactic Keyword Heuristics**: Analyzes source code tokens, package/import declarations, and function signatures.

### Common Intermediate Representation (`CIR` / `IRProgram`):
The CIR unifies parse trees into a language-independent data structure:
- **`IRProgram`**: Top-level container with lines of code, comments, functions, classes, imports, and calls.
- **`IRFunction`**: Function/method name, parameters, line boundaries, statement count, and local cyclomatic complexity.
- **`IRClass`**: Class, struct, interface, or trait definition with methods and fields.
- **`IRImport`**: Modules, includes (`#include`), and packages.
- **`IRControlFlow`**: Branches (`if`), loops (`for`/`while`), and exception blocks (`try`/`catch`).

---

## 5. Production Hardening & Developer Platform Features (Chunk 7)

### 1. Multi-File Project Analysis & ZIP Uploads (`ProjectAnalysisService`):
- Accepts multi-file payloads or raw `.zip` project archives.
- Recursively parses source files while ignoring build artifacts, virtualenvs, and VCS directories.
- Computes aggregate metrics, physical LOC, language distribution percentages, and overall codebase health scores.

### 2. Code Duplication & Clone Detection (`DuplicationDetector`):
- Normalizes token streams, whitespace, and comments across all scanned files.
- Detects Type-1 (identical), Type-2 (parameterized/renamed), and Type-3 (modified) clones with exact line boundaries and similarity percentages.

### 3. Intelligent Recommendation Engine (`RecommendationService`):
- Synthesizes findings across quality, complexity, security, and duplication.
- Provides prioritized developer guidance for refactoring complexity hotspots, decomposing large routines, and remediating security risks.

### 4. Multi-Format Report Generation (`ReportService`):
- **JSON**: Machine-readable full scan telemetry.
- **HTML**: Self-contained, responsive dashboard with dark theme and `@media print` layout.
- **PDF**: Downloadable print-ready document with formatted summary tables.

### 5. Local History Persistence (`HistoryService`):
- Stores scans locally in `.codesanitize_history/history.json`.
- Supports listing, single-scan retrieval, deletion, and purge operations.

---

## 6. Multi-Stage Pre-Acceptance Validation Pipeline (Chunk 4)

The `ValidationPipeline` coordinates 9 specialized validation stages before any transformation candidate can be committed:

1. **Syntax Integrity (`SyntaxValidator`)**: AST parsing validation.
2. **AST Structural Invariants (`AstStructuralValidator`)**: Verifies decorators, async/sync status, generator status (`yield`), exception blocks, and globals.
3. **Public Interface & Signatures (`PublicInterfaceValidator`)**: Guarantees function signatures, parameters, default values, class definitions, method contracts, and `__all__` exports remain invariant.
4. **Control-Flow Topology Invariants (`ControlFlowValidator`)**: Tracks branching/looping structures (`if/elif/else`, `for`, `while`, `try/except/finally`, `with`, `match/case`).
5. **Data-Flow & Scope Safeguards (`DataFlowValidator`)**: Hierarchical lexical scope resolution, definition-use chain verification, and prevention of undefined variable loads or parameter shadowing.
6. **Imports & Dependencies Invariants (`ImportValidator`)**: Enforces 100% strict invariance across module imports and aliases.
7. **Reflection & Eval Safeguards (`ReflectionSafeguardValidator`)**: Detects `locals()`, `globals()`, `eval()`, `exec()`, `getattr()`, `setattr()`, `__dict__`, and introspection modules.
8. **Side-Effect Sensitivity Analysis (`SideEffectValidator`)**: Static detection of file I/O, subprocess, network, environment variables, time, and concurrency.
9. **Static Behavioral Equivalence (`StaticBehaviorValidator`)**: Evaluates static return consistency.

---

## 7. Security and Scope Invariants

- **Static Analysis Only**: Code is analyzed through AST parsing and pattern recognition. User code is never executed.
- **No Arbitrary Code Execution**: Zero usage of `eval()`, `exec()`, or sub-process execution on user inputs.
- **No AI Detection or Provenance Claims**: Watermarks and non-functional artifacts are classified strictly as structural formatting traits.
