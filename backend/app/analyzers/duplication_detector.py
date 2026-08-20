"""Static Code Duplication and Clone Detection Engine.

Detects identical and near-identical functions, repeated code blocks, and structural clones
across files and within individual modules without executing code.
"""

import ast
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from app.models.schemas import DuplicationFinding, DuplicationLocation, SupportedLanguage


class DuplicationDetector:
    """Detects code clones and duplicate structures using normalized token and AST hashing."""

    @classmethod
    def detect_duplications_in_files(
        cls,
        files: List[Tuple[str, str, SupportedLanguage]],  # list of (filename, code, language)
        min_lines: int = 4,
        similarity_threshold: float = 80.0,
    ) -> List[DuplicationFinding]:
        """Detect code duplications across a list of source files."""
        findings: List[DuplicationFinding] = []
        function_registry: List[Dict] = []
        block_registry: List[Dict] = []

        # 1. Extract functions and normalized blocks from all files
        for filename, code, lang in files:
            if not code or not code.strip():
                continue

            extracted_fns = cls._extract_functions(filename, code, lang, min_lines)
            function_registry.extend(extracted_fns)

            extracted_blocks = cls._extract_code_blocks(filename, code, min_lines)
            block_registry.extend(extracted_blocks)

        # 2. Compare function pairs
        n_fns = len(function_registry)
        seen_pairs = set()

        for i in range(n_fns):
            for j in range(i + 1, n_fns):
                fn_a = function_registry[i]
                fn_b = function_registry[j]

                # Don't compare identical span in the same file
                if fn_a["filename"] == fn_b["filename"] and fn_a["line_start"] == fn_b["line_start"]:
                    continue

                pair_key = (
                    fn_a["filename"],
                    fn_a["line_start"],
                    fn_b["filename"],
                    fn_b["line_start"],
                )
                if pair_key in seen_pairs:
                    continue

                sim = cls._calculate_similarity(fn_a["normalized_body"], fn_b["normalized_body"])
                if sim >= similarity_threshold:
                    seen_pairs.add(pair_key)
                    dup_type = "exact_function" if sim >= 98.0 else "structural_clone"
                    rec = (
                        f"Extract duplicate function logic from '{fn_a['name']}' in {fn_a['filename']} "
                        f"and '{fn_b['name']}' in {fn_b['filename']} into a shared utility function."
                    )
                    findings.append(
                        DuplicationFinding(
                            similarity_percentage=round(sim, 1),
                            primary_location=DuplicationLocation(
                                filename=fn_a["filename"],
                                line_start=fn_a["line_start"],
                                line_end=fn_a["line_end"],
                                function_name=fn_a["name"],
                            ),
                            duplicate_location=DuplicationLocation(
                                filename=fn_b["filename"],
                                line_start=fn_b["line_start"],
                                line_end=fn_b["line_end"],
                                function_name=fn_b["name"],
                            ),
                            duplicate_type=dup_type,
                            snippet_preview=fn_a["snippet"][:120],
                            recommendation=rec,
                        )
                    )

        return findings

    @classmethod
    def _extract_functions(
        cls, filename: str, code: str, language: SupportedLanguage, min_lines: int
    ) -> List[Dict]:
        """Extract functions with normalized token bodies."""
        results: List[Dict] = []

        if language == SupportedLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        start = node.lineno
                        end = getattr(node, "end_lineno", node.lineno) or node.lineno
                        lines_count = end - start + 1
                        if lines_count >= min_lines:
                            fn_body_raw = "\n".join(code.splitlines()[start - 1 : end])
                            norm_body = cls._normalize_code(fn_body_raw)
                            results.append(
                                {
                                    "filename": filename,
                                    "name": node.name,
                                    "line_start": start,
                                    "line_end": end,
                                    "normalized_body": norm_body,
                                    "snippet": fn_body_raw,
                                }
                            )
                if results:
                    return results
            except Exception:
                pass

        # Regex fallback for multi-language function extraction
        lines = code.splitlines()
        pattern = re.compile(r"^\s*(?:async\s+)?(?:def|function|func|public|private|fn)\s+([a-zA-Z_]\w*)")

        current_fn = None
        start_line = 0

        for idx, line in enumerate(lines, start=1):
            m = pattern.search(line)
            if m:
                if current_fn and (idx - start_line >= min_lines):
                    raw_chunk = "\n".join(lines[start_line - 1 : idx - 1])
                    results.append(
                        {
                            "filename": filename,
                            "name": current_fn,
                            "line_start": start_line,
                            "line_end": idx - 1,
                            "normalized_body": cls._normalize_code(raw_chunk),
                            "snippet": raw_chunk,
                        }
                    )
                current_fn = m.group(1)
                start_line = idx

        if current_fn and (len(lines) - start_line + 1 >= min_lines):
            raw_chunk = "\n".join(lines[start_line - 1 :])
            results.append(
                {
                    "filename": filename,
                    "name": current_fn,
                    "line_start": start_line,
                    "line_end": len(lines),
                    "normalized_body": cls._normalize_code(raw_chunk),
                    "snippet": raw_chunk,
                }
            )

        return results

    @classmethod
    def _extract_code_blocks(
        cls, filename: str, code: str, min_lines: int, window_size: int = 6
    ) -> List[Dict]:
        """Extract sliding window code blocks for statement-level duplicate detection."""
        results: List[Dict] = []
        lines = code.splitlines()
        total_lines = len(lines)

        if total_lines < min_lines:
            return results

        step = max(min_lines // 2, 2)
        for i in range(0, total_lines - min_lines + 1, step):
            block_lines = lines[i : i + window_size]
            raw_text = "\n".join(block_lines)
            norm = cls._normalize_code(raw_text)
            if len(norm) > 30:  # Ignore trivial small blocks
                results.append(
                    {
                        "filename": filename,
                        "line_start": i + 1,
                        "line_end": min(i + window_size, total_lines),
                        "normalized_body": norm,
                        "snippet": raw_text,
                    }
                )

        return results

    @classmethod
    def _normalize_code(cls, code: str) -> str:
        """Normalize code by removing comments, whitespace variations, and string literals."""
        # 1. Remove comments
        code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)
        code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
        code = re.sub(r"/\*[\s\S]*?\*/", "", code)

        # 2. Normalize strings and numbers into generic tokens
        code = re.sub(r"(['\"]).*?\1", "$STR$", code)
        code = re.sub(r"\b\d+\b", "$NUM$", code)

        # 3. Collapse whitespace
        tokens = [t for t in re.split(r"(\W)", code) if t and not t.isspace()]
        return "".join(tokens)

    @classmethod
    def _calculate_similarity(cls, norm_a: str, norm_b: str) -> float:
        """Calculate Jaccard token n-gram similarity percentage (0 - 100%)."""
        if norm_a == norm_b:
            return 100.0

        if not norm_a or not norm_b:
            return 0.0

        n = 3
        ngrams_a = set(norm_a[i : i + n] for i in range(len(norm_a) - n + 1))
        ngrams_b = set(norm_b[i : i + n] for i in range(len(norm_b) - n + 1))

        if not ngrams_a or not ngrams_b:
            return 0.0

        intersection = len(ngrams_a.intersection(ngrams_b))
        union = len(ngrams_a.union(ngrams_b))

        return (intersection / union) * 100.0
