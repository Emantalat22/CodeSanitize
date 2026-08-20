"""Linguistic and Comment Pattern Analyzer for AI Code Provenance."""

import re
from typing import List, Set, Tuple
from app.models.schemas import SupportedLanguage
from app.provenance.models import CommentAnalysisResult, ProvenanceSignal

# Phrases that indicate legitimate developer documentation that must be preserved
PRESERVED_COMMENT_PREFIXES: Tuple[str, ...] = (
    "todo",
    "fixme",
    "note",
    "warning",
    "caution",
    "license",
    "copyright",
    "type:",
    "noqa",
    "pragma:",
    "pylint:",
    "eslint",
    "!",
)

# Comprehensive redundant / AI linguistic comment patterns
OBVIOUS_COMMENT_PATTERNS: List[Tuple[str, str, str]] = [
    # Linguistic AI intros
    (r"#\s*this\s+(?:function|script|method|module|code)\s+(?:performs|calculates|computes|takes|initializes|processes|handles|returns|demonstrates|shows|implements|provides).*", ".*", "Linguistic AI-style function description phrase"),
    (r"#\s*(?:here\s+is\s+|below\s+is\s+|the\s+following\s+is\s+)(?:the\s+)?(?:implementation|code|function|solution|logic).*", ".*", "ChatGPT-style introductory sentence"),
    (r"#\s*(?:first|next|finally|second|third),\s*(?:we\s+|we'll\s+|let's\s+)?.*", ".*", "AI-style sequential step connective phrase"),
    (r"#\s*(?:let's|we)\s+(?:define|create|implement|calculate|import|check|return|initialize|setup)\s+.*", ".*", "Textbook collaborative commentary phrasing"),
    (r"#\s*note\s+that\s+.*", ".*", "Instructional generated note phrase"),
    (r"#\s*ensure\s+(?:that\s+)?.*", ".*", "Generated sanity check comment"),
    (r"#\s*process\s+(?:the\s+)?(?:following|input|data|items|parameters|values|request).*", ".*", "Linguistic AI process directive phrase"),
    (r"#\s*initialize\s+(?:an?\s+)?(?:empty\s+)?(?:list|dict|dictionary|array|set|variable|counter|result|output|values?|data|table).*", ".*", "Obvious variable initialization comment"),
    (r"#\s*(?:loop|iterate)\s+(?:through|over|each|all|the)?\s*.*", ".*", "Loop iterator description for obvious loop"),
    (r"#\s*calculate\s+(?:the\s+)?(?:area|perimeter|sum|total|average|distance|result|values?|metrics?|statistics?|dimensions?|volume).*", ".*", "Redundant calculation description"),
    (r"#\s*compute\s+(?:the\s+)?(?:area|perimeter|sum|total|average|distance|result|values?|metrics?|statistics?|geometry|volume).*", ".*", "Redundant computation description"),
    (r"#\s*return\s+(?:the\s+)?(?:result|value|output|data|final|calculated|computed|values?|response).*", ".*", "Redundant return statement explanation"),
    (r"#\s*import\s+(?:necessary\s+|required\s+|all\s+)?(?:modules|packages|libraries|dependencies).*", ".*", "Generic import section marker"),
    (r"#\s*define\s+(?:the\s+|a\s+)?(?:function|method|class|handler).*", ".*", "Redundant definition header comment"),
    (r"#\s*function\s+to\s+.*", ".*", "Redundant function header comment"),
    (r"#\s*step\s+\d+:\s*.*", ".*", "Instructional step-by-step tutorial marker"),
    (r"#\s*check\s+if\s+.*", ".*", "Redundant conditional check description"),
    (r"#\s*print\s+(?:the\s+)?(?:result|output|message|status|values?).*", ".*", "Redundant print statement explanation"),
    (r"#\s*set\s+(?:up\s+|the\s+)?[a-zA-Z_]\w*\s+to\s+.*", ".*", "Redundant variable assignment explanation"),
    (r"#\s*(?:handle|catch)\s+(?:exceptions?|errors?).*", ".*", "Redundant exception handling comment"),
]



def is_preserved_developer_comment(comment_text: str) -> bool:
    """Check if comment contains intentional developer notes that must be preserved."""
    cleaned = comment_text.lstrip("#/ *").strip().lower()
    for prefix in PRESERVED_COMMENT_PREFIXES:
        if cleaned.startswith(prefix):
            return True
    return False


class CommentPatternAnalyzer:
    """Detects generated-style comments, redundant descriptions, and linguistic AI phrasing."""

    @classmethod
    def analyze(cls, code: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> CommentAnalysisResult:
        """Perform deterministic static analysis of code comments."""
        lines = code.splitlines()
        total_lines = len(lines)
        comment_lines_count = 0
        signals: List[ProvenanceSignal] = []

        # Find comment lines and check for patterns
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Single-line comment detection (Python # or JS/C/Java //)
            is_comment = False
            comment_text = ""
            if stripped.startswith("#"):
                is_comment = True
                comment_text = stripped
            elif stripped.startswith("//"):
                is_comment = True
                comment_text = stripped
            elif "/*" in stripped and "*/" in stripped:
                is_comment = True
                comment_text = stripped

            if is_comment:
                comment_lines_count += 1
                if is_preserved_developer_comment(comment_text):
                    continue

                for comment_regex, next_code_regex, description in OBVIOUS_COMMENT_PATTERNS:
                    if re.match(comment_regex, comment_text, re.IGNORECASE):
                        signals.append(
                            ProvenanceSignal(
                                signal_type="redundant_comment",
                                severity="medium" if ("step" in comment_text.lower() or "performs" in comment_text.lower()) else "low",
                                confidence=0.88,
                                description=f"AI Linguistic Fingerprint: {description}",
                                file_location={"line_start": idx, "line_end": idx},
                                evidence=comment_text,
                            )
                        )
                        break

        # Check for generic/repetitive docstring templates on trivial functions
        docstring_matches = re.findall(r'"""\s*([^\n]+)\n\s*(?:Args|Parameters|Returns):', code, re.IGNORECASE)
        if len(docstring_matches) >= 2:
            signals.append(
                ProvenanceSignal(
                    signal_type="repetitive_docstring_template",
                    severity="low",
                    confidence=0.75,
                    description=f"Found {len(docstring_matches)} textbook-scaffolded docstring templates",
                    evidence=docstring_matches[0][:80],
                )
            )

        comment_ratio = round(comment_lines_count / max(total_lines, 1), 3)

        return CommentAnalysisResult(
            total_comments=comment_lines_count,
            redundant_comments_count=len(signals),
            obvious_comments=signals,
            comment_ratio=comment_ratio,
        )
