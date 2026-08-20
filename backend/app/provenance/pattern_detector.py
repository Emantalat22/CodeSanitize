"""Comprehensive Multi-Vector AI Pattern & Watermark Detector for CodeSanitize."""

import ast
import math
import re
from typing import Any, Dict, List, Tuple
from app.models.schemas import SupportedLanguage
from app.provenance.comment_analyzer import is_preserved_developer_comment
from app.provenance.models import ProvenanceSignal


def calculate_shannon_entropy(text: str) -> float:
    """Computes Shannon entropy (bits per character) of token distribution."""
    if not text:
        return 0.0
    freq: Dict[str, int] = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    total = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 3)


class AIPatternDetector:
    """Multi-layer static detector for AI-style writing, structural boilerplate, and code entropy."""

    GENERIC_NAMES = {
        "temp", "temp_var", "temp_value", "temp_data", "temp_list", "temp_dict",
        "result", "result_data", "res_val", "result_list", "result_dict", "final_result",
        "data_list", "data_dict", "my_list", "my_dict", "item_list",
        "output_value", "processed_data", "processed_output", "output_data", "calc_result",
        "var_1", "var_2", "item_1", "item_2", "param_1", "param_2",
        "input_val", "input_data", "element_val", "current_item", "total_sum",
    }

    LINGUISTIC_PHRASES = [
        (r"#\s*this\s+(?:function|script|method|module|code)\s+(?:performs|calculates|computes|takes|initializes|processes|handles|returns|demonstrates|shows|implements|provides).*", "This function performs/calculates phrase", "PROV-COMMENT-NORM-01"),
        (r"#\s*(?:here\s+is\s+|below\s+is\s+|the\s+following\s+is\s+)(?:the\s+)?(?:implementation|code|function|solution|logic).*", "ChatGPT-style introductory sentence", "PROV-COMMENT-NORM-01"),
        (r"#\s*(?:first|next|finally|second|third),\s*(?:we\s+|we'll\s+|let's\s+)?.*", "AI-style sequential step connective phrase", "PROV-COMMENT-NORM-01"),
        (r"#\s*(?:let's|we)\s+(?:define|create|implement|calculate|import|check|return|initialize|setup)\s+.*", "Textbook collaborative commentary phrasing", "PROV-COMMENT-NORM-01"),
        (r"#\s*note\s+that\s+.*", "Instructional generated note phrase", "PROV-COMMENT-NORM-01"),
        (r"#\s*ensure\s+(?:that\s+)?.*", "Generated sanity check comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*process\s+(?:the\s+)?(?:following|input|data|items|parameters|values|request).*", "Process the following/input directive", "PROV-COMMENT-NORM-01"),
        (r"#\s*initialize\s+(?:an?\s+)?(?:empty\s+)?(?:list|dict|dictionary|array|set|variable|counter|result|output|values?|data|table).*", "Initialize empty variable comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*(?:loop|iterate)\s+(?:through|over|each|all|the)?\s*.*", "Loop iterator description for obvious loop", "PROV-COMMENT-NORM-01"),
        (r"#\s*calculate\s+(?:the\s+)?(?:area|perimeter|sum|total|average|distance|result|values?|metrics?|statistics?|dimensions?|volume).*", "Calculate the formula comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*compute\s+(?:the\s+)?(?:area|perimeter|sum|total|average|distance|result|values?|metrics?|statistics?|geometry|volume).*", "Compute the metric comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*return\s+(?:the\s+)?(?:result|value|output|data|final|calculated|computed|values?|response).*", "Return the calculated result explanation", "PROV-COMMENT-NORM-01"),
        (r"#\s*step\s+\d+:\s*.*", "Instructional step-by-step tutorial marker", "PROV-COMMENT-NORM-01"),
        (r"#\s*import\s+(?:necessary\s+|required\s+|all\s+)?(?:modules|packages|libraries|dependencies).*", "Import necessary packages marker", "PROV-COMMENT-NORM-01"),
        (r"#\s*define\s+(?:the\s+|a\s+)?(?:function|method|class|handler).*", "Define function header comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*function\s+to\s+.*", "Redundant function header comment", "PROV-COMMENT-NORM-01"),
        (r"#\s*check\s+if\s+.*", "Check if conditional description", "PROV-COMMENT-NORM-01"),
        (r"#\s*print\s+(?:the\s+)?(?:result|output|message|status).*", "Print output statement comment", "PROV-COMMENT-NORM-01"),
    ]


    BOILERPLATE_TEMPLATES = [
        (r"try:\s*\n\s+.*\n\s*except\s+Exception\s+as\s+e:\s*\n\s+print\(.*e.*\)", "Formulaic generic exception print handler", "PY-STRUCT-SIMPLIFY-01"),
        (r"if\s+__name__\s*==\s*['\"]__main__['\"]:\s*\n(?:\s+.*=[^\n]+\n)+\s*print\(", "Textbook demonstration execution entrypoint", "PY-STRUCT-SIMPLIFY-01"),
        (r'"""\s*([A-Za-z\s]+)\.\s*\n\s*(?:Args|Parameters|Arguments):\s*\n(?:\s+[a-zA-Z_]\w*\s*\([^)]*\):[^\n]+\n)+\s*(?:Returns|Yields):', "Formulaic textbook docstring scaffolding on small function", "PROV-COMMENT-NORM-01"),
    ]

    @classmethod
    def analyze(cls, code: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> Dict[str, Any]:
        """Perform multi-vector AI watermark and pattern analysis."""
        lines = code.splitlines()
        total_lines = len(lines)
        signals: List[ProvenanceSignal] = []

        if not code.strip() or total_lines == 0:
            return {
                "ai_pattern_score": 0,
                "confidence_level": "high",
                "confidence_score": 0.95,
                "signals": [],
                "breakdown": {
                    "linguistic_fingerprints_count": 0,
                    "generic_identifiers_count": 0,
                    "structural_fingerprints_count": 0,
                    "boilerplate_templates_count": 0,
                    "low_entropy_regularity_count": 0,
                    "shannon_entropy": 0.0,
                },
                "recommendations": ["Source code is empty; zero synthetic patterns detected."],
            }

        # 1. Linguistic & AI Writing Fingerprints
        linguistic_count = 0
        comment_lines_count = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                comment_lines_count += 1
                if is_preserved_developer_comment(stripped):
                    continue

                for regex, desc, rule_id in cls.LINGUISTIC_PHRASES:
                    if re.match(regex, stripped, re.IGNORECASE):
                        linguistic_count += 1
                        signals.append(
                            ProvenanceSignal(
                                signal_type="linguistic_fingerprint",
                                severity="medium" if ("step" in stripped.lower() or "performs" in stripped.lower()) else "low",
                                confidence=0.88,
                                description=f"AI Linguistic Phrase: {desc} (Remediated by {rule_id})",
                                file_location={"line_start": idx, "line_end": idx},
                                evidence=stripped,
                            )
                        )
                        break

        # 2. Generic & AI Formulaic Identifiers
        naming_count = 0
        if language == SupportedLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        name_lower = node.id.lower()
                        if name_lower in cls.GENERIC_NAMES or re.match(r"^(?:temp|result|data|item|var|val)_\w+$", name_lower):
                            naming_count += 1
                            signals.append(
                                ProvenanceSignal(
                                    signal_type="generic_identifier",
                                    severity="medium",
                                    confidence=0.85,
                                    description=f"Generic AI identifier '{node.id}' (Remediated by PY-SAFE-LOCAL-RENAME-01)",
                                    file_location={"line_start": getattr(node, "lineno", None)},
                                    evidence=node.id,
                                )
                            )
            except Exception:
                pass

        if naming_count == 0:
            for match in re.finditer(r"\b([a-zA-Z_]\w*)\b", code):
                w = match.group(1).lower()
                if w in cls.GENERIC_NAMES:
                    naming_count += 1
                    signals.append(
                        ProvenanceSignal(
                            signal_type="generic_identifier",
                            severity="low",
                            confidence=0.75,
                            description=f"Generic AI identifier '{match.group(1)}' (Remediated by PY-SAFE-LOCAL-RENAME-01)",
                            evidence=match.group(1),
                        )
                    )

        # 3. Structural Fingerprint Analysis (Temporary Chains & Dictionary Accumulators)
        structural_count = 0
        if language == SupportedLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    # Pattern: x = {}; x['k'] = v; return x
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        stmts = node.body
                        for s_idx, stmt in enumerate(stmts):
                            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                                if isinstance(stmt.value, ast.Dict) and len(stmt.value.keys) == 0:
                                    # Found empty dict initialization inside function
                                    dict_name = stmt.targets[0].id
                                    if s_idx + 1 < len(stmts):
                                        structural_count += 1
                                        signals.append(
                                            ProvenanceSignal(
                                                signal_type="structural_fingerprint",
                                                severity="medium",
                                                confidence=0.90,
                                                description=f"Textbook sequential dictionary construction for '{dict_name}' (Remediated by PY-STRUCT-SIMPLIFY-01)",
                                                file_location={"line_start": getattr(stmt, "lineno", None)},
                                                evidence=f"{dict_name} = {{}}",
                                            )
                                        )
                                # Pattern: single-use return variable (res = expr; return res)
                                elif s_idx + 1 < len(stmts):
                                    next_s = stmts[s_idx + 1]
                                    if isinstance(next_s, ast.Return) and isinstance(next_s.value, ast.Name):
                                        if next_s.value.id == stmt.targets[0].id:
                                            structural_count += 1
                                            signals.append(
                                                ProvenanceSignal(
                                                    signal_type="structural_fingerprint",
                                                    severity="low",
                                                    confidence=0.85,
                                                    description=f"Redundant single-use return variable '{stmt.targets[0].id}' (Remediated by PY-STRUCT-SIMPLIFY-01)",
                                                    file_location={"line_start": getattr(stmt, "lineno", None)},
                                                    evidence=f"{stmt.targets[0].id} = ...; return {stmt.targets[0].id}",
                                                )
                                            )
            except Exception:
                pass

        # 4. Boilerplate Templates
        boilerplate_count = 0
        for template_regex, desc, rule_id in cls.BOILERPLATE_TEMPLATES:
            for match in re.finditer(template_regex, code, re.MULTILINE):
                boilerplate_count += 1
                snippet = match.group(0)
                signals.append(
                    ProvenanceSignal(
                        signal_type="boilerplate_template",
                        severity="medium",
                        confidence=0.80,
                        description=f"Synthetic boilerplate pattern: {desc} (Remediated by {rule_id})",
                        evidence=snippet[:80] + ("..." if len(snippet) > 80 else ""),
                    )
                )

        # 5. Code Entropy & Predictability Vector
        entropy_val = calculate_shannon_entropy(code)
        low_entropy_count = 0
        if 0 < entropy_val < 4.2 and total_lines > 10:
            low_entropy_count += 1
            signals.append(
                ProvenanceSignal(
                    signal_type="code_entropy_regularity",
                    severity="low",
                    confidence=0.70,
                    description=f"Low Shannon entropy ({entropy_val} bits/char) indicates predictable synthetic token distribution",
                    evidence=f"Entropy: {entropy_val}",
                )
            )

        # 6. Formatting & Whitespace Fingerprint Vector
        formatting_count = 0
        consecutive_blanks = 0
        for line in lines:
            if not line.strip():
                consecutive_blanks += 1
                if consecutive_blanks >= 2:
                    formatting_count += 1
            else:
                consecutive_blanks = 0

        if formatting_count > 0:
            signals.append(
                ProvenanceSignal(
                    signal_type="formatting_fingerprint",
                    severity="low",
                    confidence=0.99,
                    description=f"Excessive vertical whitespace ({formatting_count} redundant blank line(s)) (Remediated by PY-FMT-NORM-01)",
                    evidence=f"{formatting_count} redundant blank line(s)",
                )
            )

        # Compute Composite AI Fingerprint Score (0 - 100)
        has_primary_watermarks = (linguistic_count + naming_count + structural_count + boilerplate_count) > 0
        if not has_primary_watermarks:
            low_entropy_count = 0
            signals = [s for s in signals if getattr(s, "signal_type", "") != "code_entropy_regularity"]

        score_ling = min(linguistic_count * 10, 35)
        score_naming = min(naming_count * 10, 30)
        score_struct = min(structural_count * 15, 30)
        score_boiler = min(boilerplate_count * 10, 20)
        score_entropy = min(low_entropy_count * 10, 15) if has_primary_watermarks else 0
        score_fmt = min(formatting_count * 5, 15)

        raw_score = score_ling + score_naming + score_struct + score_boiler + score_entropy + score_fmt
        ai_pattern_score = min(max(raw_score, 0), 100)



        # Confidence calculation
        if total_lines < 8:
            confidence_level = "low"
            confidence_score = 0.65
        elif len(signals) >= 3 or total_lines > 25:
            confidence_level = "high"
            confidence_score = 0.94
        else:
            confidence_level = "medium"
            confidence_score = 0.80

        # Actionable recommendations
        recommendations: List[str] = []
        if linguistic_count > 0:
            recommendations.append(
                f"Strip {linguistic_count} obvious AI linguistic phrases ('This function performs...', 'Initialize empty...') using PROV-COMMENT-NORM-01."
            )
        if naming_count > 0:
            recommendations.append(
                f"Replace {naming_count} generic formulaic identifiers ('result_data', 'temp_area') with contextual human names using PY-SAFE-LOCAL-RENAME-01."
            )
        if structural_count > 0:
            recommendations.append(
                f"Simplify {structural_count} textbook dictionary accumulations and inlined return variables using PY-STRUCT-SIMPLIFY-01."
            )
        if not recommendations:
            recommendations.append("Code exhibits natural, experienced-developer human patterns with zero detectable synthetic traits.")

        return {
            "ai_pattern_score": ai_pattern_score,
            "confidence_level": confidence_level,
            "confidence_score": confidence_score,
            "signals": signals,
            "breakdown": {
                "linguistic_fingerprints_count": linguistic_count,
                "generic_identifiers_count": naming_count,
                "structural_fingerprints_count": structural_count,
                "boilerplate_templates_count": boilerplate_count,
                "low_entropy_regularity_count": low_entropy_count,
                "shannon_entropy": entropy_val,
                "generic_comments_count": linguistic_count,
                "repetitive_naming_count": naming_count,
                "boilerplate_structures_count": boilerplate_count,
                "predictable_templates_count": boilerplate_count,
                "unnatural_formatting_count": low_entropy_count,
                "repeated_blocks_count": structural_count,
            },

            "recommendations": recommendations,
        }
