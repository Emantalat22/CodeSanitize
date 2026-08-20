"""Non-functional artifact analyzer for inspecting code formatting and character-level properties."""

import re
import unicodedata
from typing import List, Optional
from app.models.schemas import (
    ArtifactCategory,
    NonFunctionalArtifact,
    SupportedLanguage,
)

# Invisible / Zero-width / Format Unicode Characters
UNUSUAL_UNICODE_MAP = {
    "\u200B": ("Zero-Width Space", "U+200B"),
    "\u200C": ("Zero-Width Non-Joiner", "U+200C"),
    "\u200D": ("Zero-Width Joiner", "U+200D"),
    "\u200E": ("Left-to-Right Mark", "U+200E"),
    "\u200F": ("Right-to-Left Mark", "U+200F"),
    "\uFEFF": ("Zero-Width No-Break Space (BOM)", "U+FEFF"),
    "\u202A": ("Left-to-Right Embedding", "U+202A"),
    "\u202B": ("Right-to-Left Embedding", "U+202B"),
    "\u202C": ("Pop Directional Formatting", "U+202C"),
    "\u202D": ("Left-to-Right Override", "U+202D"),
    "\u202E": ("Right-to-Left Override", "U+202E"),
    "\u2066": ("Left-to-Right Isolate", "U+2066"),
    "\u2067": ("Right-to-Left Isolate", "U+2067"),
    "\u2068": ("First Strong Isolate", "U+2068"),
    "\u2069": ("Pop Directional Isolate", "U+2069"),
    "\u00A0": ("Non-Breaking Space", "U+00A0"),
    "\u2000": ("En Quad Space", "U+2000"),
    "\u2001": ("Em Quad Space", "U+2001"),
    "\u2002": ("En Space", "U+2002"),
    "\u2003": ("Em Space", "U+2003"),
    "\u2004": ("Three-Per-Em Space", "U+2004"),
    "\u2005": ("Four-Per-Em Space", "U+2005"),
    "\u2006": ("Six-Per-Em Space", "U+2006"),
    "\u2007": ("Figure Space", "U+2007"),
    "\u2008": ("Punctuation Space", "U+2008"),
    "\u2009": ("Thin Space", "U+2009"),
    "\u200A": ("Hair Space", "U+200A"),
    "\u202F": ("Narrow No-Break Space", "U+202F"),
    "\u3000": ("Ideographic Space", "U+3000"),
}

# Regex for source encoding declaration (e.g. Python PEP 263)
ENCODING_DECLARATION_RE = re.compile(
    r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)", re.MULTILINE
)


class NonFunctionalAnalyzer:
    """Conservative analyzer for non-functional code formatting and character-level properties."""

    @classmethod
    def analyze(
        cls,
        code: str,
        language: SupportedLanguage,
        comment_count: int = 0,
        docstring_count: int = 0,
    ) -> List[NonFunctionalArtifact]:
        """Detect formatting artifacts, unusual Unicode characters, whitespace anomalies, and encoding marks.

        Args:
            code: Raw source code text.
            language: Programming language.
            comment_count: Count of comments already determined by parser.
            docstring_count: Count of docstrings already determined by parser.

        Returns:
            List of detected NonFunctionalArtifact items.
        """
        artifacts: List[NonFunctionalArtifact] = []
        if not code:
            return artifacts

        lines = code.splitlines(keepends=False)

        # 1. Trailing Whitespace Analysis
        trailing_lines: List[int] = []
        for idx, line in enumerate(lines, start=1):
            if line.endswith(" ") or line.endswith("\t"):
                trailing_lines.append(idx)

        if trailing_lines:
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.WHITESPACE,
                    kind="trailing_whitespace",
                    description=f"Found trailing whitespace on {len(trailing_lines)} line(s)",
                    count=len(trailing_lines),
                    details={
                        "affected_lines": trailing_lines[:20],
                        "total_affected_lines": len(trailing_lines),
                    },
                )
            )

        # 2. Mixed Tab and Space Indentation
        tab_indented_lines: List[int] = []
        space_indented_lines: List[int] = []
        mixed_indent_lines: List[int] = []

        for idx, line in enumerate(lines, start=1):
            leading_whitespace = line[: len(line) - len(line.lstrip(" \t"))]
            if not leading_whitespace:
                continue

            has_space = " " in leading_whitespace
            has_tab = "\t" in leading_whitespace

            if has_space and has_tab:
                mixed_indent_lines.append(idx)
            elif has_tab:
                tab_indented_lines.append(idx)
            elif has_space:
                space_indented_lines.append(idx)

        if mixed_indent_lines:
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.WHITESPACE,
                    kind="mixed_indentation",
                    description=f"Mixed spaces and tabs within the same line indentation on {len(mixed_indent_lines)} line(s)",
                    count=len(mixed_indent_lines),
                    details={"affected_lines": mixed_indent_lines[:15]},
                )
            )
        elif tab_indented_lines and space_indented_lines:
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.WHITESPACE,
                    kind="inconsistent_indentation_style",
                    description=f"File contains inconsistent indentation style ({len(space_indented_lines)} space-indented vs {len(tab_indented_lines)} tab-indented lines)",
                    count=len(tab_indented_lines) + len(space_indented_lines),
                    details={
                        "space_lines_sample": space_indented_lines[:5],
                        "tab_lines_sample": tab_indented_lines[:5],
                    },
                )
            )

        # 3. Excessive Consecutive Blank Lines (>= 3 consecutive empty lines)
        consecutive_blank_count = 0
        excessive_blank_clusters: List[dict] = []
        cluster_start: Optional[int] = None

        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                if consecutive_blank_count == 0:
                    cluster_start = idx
                consecutive_blank_count += 1
            else:
                if consecutive_blank_count >= 3 and cluster_start is not None:
                    excessive_blank_clusters.append(
                        {
                            "start_line": cluster_start,
                            "end_line": idx - 1,
                            "count": consecutive_blank_count,
                        }
                    )
                consecutive_blank_count = 0
                cluster_start = None

        if consecutive_blank_count >= 3 and cluster_start is not None:
            excessive_blank_clusters.append(
                {
                    "start_line": cluster_start,
                    "end_line": len(lines),
                    "count": consecutive_blank_count,
                }
            )

        if excessive_blank_clusters:
            total_excessive = sum(c["count"] for c in excessive_blank_clusters)
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.FORMATTING,
                    kind="excessive_blank_lines",
                    description=f"Detected {len(excessive_blank_clusters)} cluster(s) of 3+ consecutive blank lines (total {total_excessive} empty lines)",
                    count=len(excessive_blank_clusters),
                    details={"clusters": excessive_blank_clusters},
                )
            )

        # 4. Unusual / Invisible Unicode Character Detection
        unusual_char_counts: dict[str, int] = {}
        unusual_char_locations: dict[str, List[dict]] = {}

        for line_num, line in enumerate(lines, start=1):
            for col_num, char in enumerate(line, start=1):
                if char in UNUSUAL_UNICODE_MAP:
                    name, codepoint = UNUSUAL_UNICODE_MAP[char]
                    key = f"{name} ({codepoint})"
                    unusual_char_counts[key] = unusual_char_counts.get(key, 0) + 1
                    if key not in unusual_char_locations:
                        unusual_char_locations[key] = []
                    if len(unusual_char_locations[key]) < 10:
                        unusual_char_locations[key].append(
                            {"line": line_num, "column": col_num}
                        )

        for key, count in unusual_char_counts.items():
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.UNICODE,
                    kind="unusual_unicode_character",
                    description=f"Detected {count} instance(s) of invisible or special Unicode character: {key}",
                    count=count,
                    details={"locations": unusual_char_locations.get(key, [])},
                )
            )

        # 5. Source Encoding Declarations
        encoding_match = ENCODING_DECLARATION_RE.search(code)
        if encoding_match:
            encoding_name = encoding_match.group(1)
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.ENCODING,
                    kind="source_encoding_declaration",
                    description=f"Found explicit source encoding declaration: '{encoding_name}'",
                    character=encoding_match.group(0),
                    count=1,
                    details={"encoding": encoding_name},
                )
            )

        # 6. Comments Inventory
        if comment_count > 0:
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.COMMENTS,
                    kind="comments_present",
                    description=f"Source contains {comment_count} comment block(s) or line(s)",
                    count=comment_count,
                    details={"language": language.value},
                )
            )

        # 7. Docstrings Inventory
        if docstring_count > 0:
            artifacts.append(
                NonFunctionalArtifact(
                    category=ArtifactCategory.COMMENTS,
                    kind="docstrings_present",
                    description=f"Source contains {docstring_count} structured docstring(s)",
                    count=docstring_count,
                    details={"language": language.value},
                )
            )

        return artifacts
