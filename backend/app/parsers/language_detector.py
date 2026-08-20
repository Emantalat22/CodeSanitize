"""Automatic programming language detection engine.

Analyzes filename extensions, shebang header lines, and source code syntactic keywords
to identify Python, JavaScript, TypeScript, Java, C++, C, Go, Rust, Ruby, PHP, and C#.
"""

import os
import re
from typing import Optional
from app.models.schemas import SupportedLanguage


class LanguageDetector:
    """Detects target programming language using tiered deterministic heuristics."""

    EXTENSION_MAP = {
        ".py": SupportedLanguage.PYTHON,
        ".pyw": SupportedLanguage.PYTHON,
        ".js": SupportedLanguage.JAVASCRIPT,
        ".jsx": SupportedLanguage.JAVASCRIPT,
        ".mjs": SupportedLanguage.JAVASCRIPT,
        ".cjs": SupportedLanguage.JAVASCRIPT,
        ".ts": SupportedLanguage.TYPESCRIPT,
        ".tsx": SupportedLanguage.TYPESCRIPT,
        ".mts": SupportedLanguage.TYPESCRIPT,
        ".cts": SupportedLanguage.TYPESCRIPT,
        ".java": SupportedLanguage.JAVA,
        ".cpp": SupportedLanguage.CPP,
        ".cc": SupportedLanguage.CPP,
        ".cxx": SupportedLanguage.CPP,
        ".hpp": SupportedLanguage.CPP,
        ".hxx": SupportedLanguage.CPP,
        ".h": SupportedLanguage.C,
        ".c": SupportedLanguage.C,
        ".go": SupportedLanguage.GO,
        ".rs": SupportedLanguage.RUST,
        ".cs": SupportedLanguage.CSHARP,
        ".rb": SupportedLanguage.RUBY,
        ".php": SupportedLanguage.PHP,
    }

    SHEBANG_MAP = [
        (r"^#!\s*/.*\bpython[23]?\b", SupportedLanguage.PYTHON),
        (r"^#!\s*/.*\bnode\b", SupportedLanguage.JAVASCRIPT),
        (r"^#!\s*/.*\bdeno\b", SupportedLanguage.TYPESCRIPT),
        (r"^#!\s*/.*\bruby\b", SupportedLanguage.RUBY),
        (r"^#!\s*/.*\bphp\b", SupportedLanguage.PHP),
    ]

    @classmethod
    def detect(cls, code: str, filename: Optional[str] = None) -> SupportedLanguage:
        """Detect language with tiered fallback: Extension -> Shebang -> Syntax Heuristics."""
        # Tier 1: Explicit Filename Extension
        if filename:
            ext_lang = cls.detect_from_filename(filename)
            if ext_lang:
                return ext_lang

        # Tier 2: Shebang Line
        shebang_lang = cls.detect_from_shebang(code)
        if shebang_lang:
            return shebang_lang

        # Tier 3: Syntactic Pattern Heuristics
        return cls.detect_from_syntax(code)

    @classmethod
    def detect_from_filename(cls, filename: str) -> Optional[SupportedLanguage]:
        """Detect language based on filename extension."""
        if not filename:
            return None
        base = os.path.basename(filename).lower()
        _, ext = os.path.splitext(base)
        return cls.EXTENSION_MAP.get(ext)

    @classmethod
    def detect_from_shebang(cls, code: str) -> Optional[SupportedLanguage]:
        """Detect language based on #! shebang in first line."""
        if not code or not code.startswith("#!"):
            return None

        first_line = code.splitlines()[0] if code else ""
        for pattern, lang in cls.SHEBANG_MAP:
            if re.search(pattern, first_line):
                return lang
        return None

    @classmethod
    def detect_from_syntax(cls, code: str) -> SupportedLanguage:
        """Analyze code tokens, imports, and keywords to determine the language."""
        if not code or not code.strip():
            return SupportedLanguage.PYTHON  # Default baseline for empty code

        # Scoring weights for distinct language signatures
        scores = {
            SupportedLanguage.PYTHON: 0,
            SupportedLanguage.JAVASCRIPT: 0,
            SupportedLanguage.TYPESCRIPT: 0,
            SupportedLanguage.JAVA: 0,
            SupportedLanguage.CPP: 0,
            SupportedLanguage.C: 0,
            SupportedLanguage.GO: 0,
            SupportedLanguage.RUST: 0,
            SupportedLanguage.PHP: 0,
            SupportedLanguage.RUBY: 0,
            SupportedLanguage.CSHARP: 0,
        }

        # 1. PHP
        if "<?php" in code:
            scores[SupportedLanguage.PHP] += 20
        if re.search(r"\$\w+\s*->", code):
            scores[SupportedLanguage.PHP] += 5

        # 2. Go
        if re.search(r"\bpackage\s+[a-zA-Z_]\w*", code):
            scores[SupportedLanguage.GO] += 15
        if re.search(r"\bfunc\s+(\([^\)]+\)\s*)?[a-zA-Z_]\w*\(", code):
            scores[SupportedLanguage.GO] += 8
        if 'import "fmt"' in code or 'import (' in code:
            scores[SupportedLanguage.GO] += 6

        # 3. Rust
        if re.search(r"\bfn\s+[a-zA-Z_]\w*\s*\(", code):
            scores[SupportedLanguage.RUST] += 10
        if "println!" in code or "format!" in code or "vec!" in code:
            scores[SupportedLanguage.RUST] += 10
        if "pub struct " in code or "impl " in code or "let mut " in code:
            scores[SupportedLanguage.RUST] += 8

        # 4. Java
        if "public class " in code or "public static void main" in code:
            scores[SupportedLanguage.JAVA] += 15
        if "System.out.println" in code:
            scores[SupportedLanguage.JAVA] += 10
        if re.search(r"\bpackage\s+[a-zA-Z0-9_.]+;", code):
            scores[SupportedLanguage.JAVA] += 8

        # 5. C++
        if "#include <iostream>" in code or "#include <vector>" in code or "std::cout" in code:
            scores[SupportedLanguage.CPP] += 15
        if "template<typename" in code or "namespace " in code or "std::string" in code:
            scores[SupportedLanguage.CPP] += 10

        # 6. C
        if "#include <stdio.h>" in code or "#include <stdlib.h>" in code:
            scores[SupportedLanguage.C] += 15
        if "printf(" in code or "int main(int argc, char" in code:
            scores[SupportedLanguage.C] += 8

        # 7. TypeScript
        if re.search(r"\binterface\s+[A-Z]\w*\s*\{", code) or re.search(r"\btype\s+[A-Z]\w*\s*=", code):
            scores[SupportedLanguage.TYPESCRIPT] += 15
        if re.search(r":\s*(string|number|boolean|any|void|unknown)\b", code):
            scores[SupportedLanguage.TYPESCRIPT] += 8

        # 8. JavaScript
        if "console.log" in code or "require(" in code or "module.exports" in code:
            scores[SupportedLanguage.JAVASCRIPT] += 8
        if re.search(r"\b(const|let|var)\s+\w+\s*=", code):
            scores[SupportedLanguage.JAVASCRIPT] += 6
        if re.search(r"\bfunction\s+\w+\s*\(", code):
            scores[SupportedLanguage.JAVASCRIPT] += 5

        # 9. Python
        if re.search(r"\bdef\s+[a-zA-Z_]\w*\s*\(.*?\)\s*:", code):
            scores[SupportedLanguage.PYTHON] += 15
        if re.search(r"\bclass\s+[a-zA-Z_]\w*(\(.*?\))?\s*:", code):
            scores[SupportedLanguage.PYTHON] += 10
        if 'if __name__ == "__main__":' in code or "if __name__ == '__main__':" in code:
            scores[SupportedLanguage.PYTHON] += 12
        if "import os" in code or "import sys" in code or "from typing import" in code:
            scores[SupportedLanguage.PYTHON] += 8
        if re.search(r"\belif\s+.*?:", code):
            scores[SupportedLanguage.PYTHON] += 8

        # 10. Ruby
        if re.search(r"\bdef\s+[a-zA-Z_]\w*\b[^\:]*$", code, re.MULTILINE):
            scores[SupportedLanguage.RUBY] += 5
        if "attr_accessor" in code or "require_relative" in code or "puts " in code:
            scores[SupportedLanguage.RUBY] += 8

        # 11. C#
        if "using System;" in code or "Console.WriteLine" in code:
            scores[SupportedLanguage.CSHARP] += 12

        # Pick highest score
        best_lang = max(scores.items(), key=lambda item: item[1])
        if best_lang[1] > 0:
            return best_lang[0]

        return SupportedLanguage.PYTHON
