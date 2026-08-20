"""Parser registry for language parser discovery, automatic detection, and dispatch."""

from typing import Dict, List, Optional
from app.models.schemas import LanguageInfo, PipelineStatus, SupportedLanguage
from app.parsers.base import BaseLanguageParser
from app.parsers.language_detector import LanguageDetector
from app.parsers.python_parser import PythonParser
from app.parsers.tree_sitter_parser import TreeSitterParser


class ParserRegistry:
    """Registry maintaining available language parsers and their runtime statuses."""

    _parsers: Dict[SupportedLanguage, BaseLanguageParser] = {}

    @classmethod
    def initialize(cls):
        """Initialize and register default language parser adapters."""
        cls._parsers[SupportedLanguage.PYTHON] = PythonParser()
        cls._parsers[SupportedLanguage.JAVASCRIPT] = TreeSitterParser(
            SupportedLanguage.JAVASCRIPT, "JavaScript"
        )
        cls._parsers[SupportedLanguage.TYPESCRIPT] = TreeSitterParser(
            SupportedLanguage.TYPESCRIPT, "TypeScript"
        )
        cls._parsers[SupportedLanguage.JAVA] = TreeSitterParser(
            SupportedLanguage.JAVA, "Java"
        )
        cls._parsers[SupportedLanguage.CPP] = TreeSitterParser(
            SupportedLanguage.CPP, "C++"
        )
        cls._parsers[SupportedLanguage.C] = TreeSitterParser(
            SupportedLanguage.C, "C"
        )
        cls._parsers[SupportedLanguage.GO] = TreeSitterParser(
            SupportedLanguage.GO, "Go"
        )
        cls._parsers[SupportedLanguage.RUST] = TreeSitterParser(
            SupportedLanguage.RUST, "Rust"
        )
        cls._parsers[SupportedLanguage.CSHARP] = TreeSitterParser(
            SupportedLanguage.CSHARP, "C#"
        )
        cls._parsers[SupportedLanguage.RUBY] = TreeSitterParser(
            SupportedLanguage.RUBY, "Ruby"
        )
        cls._parsers[SupportedLanguage.PHP] = TreeSitterParser(
            SupportedLanguage.PHP, "PHP"
        )

    @classmethod
    def get_parser(cls, language: SupportedLanguage) -> Optional[BaseLanguageParser]:
        """Retrieve parser instance for the specified language."""
        if not cls._parsers:
            cls.initialize()
        return cls._parsers.get(language)

    @classmethod
    def detect_language(cls, code: str, filename: Optional[str] = None) -> SupportedLanguage:
        """Automatically detect language from code and filename."""
        return LanguageDetector.detect(code, filename)

    @classmethod
    def is_language_supported(cls, language: SupportedLanguage) -> bool:
        """Check if language has a registered parser."""
        if not cls._parsers:
            cls.initialize()
        return language in cls._parsers

    @classmethod
    def get_language_infos(cls) -> List[LanguageInfo]:
        """Retrieve status manifest for all supported languages."""
        if not cls._parsers:
            cls.initialize()

        languages_metadata = [
            (
                SupportedLanguage.PYTHON,
                "Python",
                [".py", ".pyw"],
                "Native AST / Tokenizer",
            ),
            (
                SupportedLanguage.JAVASCRIPT,
                "JavaScript",
                [".js", ".mjs", ".cjs"],
                "Tree-sitter JavaScript",
            ),
            (
                SupportedLanguage.TYPESCRIPT,
                "TypeScript",
                [".ts", ".tsx"],
                "Tree-sitter TypeScript",
            ),
            (
                SupportedLanguage.JAVA,
                "Java",
                [".java"],
                "Tree-sitter Java",
            ),
            (
                SupportedLanguage.CPP,
                "C++",
                [".cpp", ".cc", ".cxx", ".hpp", ".h"],
                "Tree-sitter C++",
            ),
            (
                SupportedLanguage.C,
                "C",
                [".c", ".h"],
                "Tree-sitter C",
            ),
            (
                SupportedLanguage.GO,
                "Go",
                [".go"],
                "Tree-sitter Go / CIR",
            ),
            (
                SupportedLanguage.RUST,
                "Rust",
                [".rs"],
                "Tree-sitter Rust / CIR",
            ),
            (
                SupportedLanguage.CSHARP,
                "C#",
                [".cs"],
                "Unified CIR C#",
            ),
            (
                SupportedLanguage.RUBY,
                "Ruby",
                [".rb"],
                "Unified CIR Ruby",
            ),
            (
                SupportedLanguage.PHP,
                "PHP",
                [".php"],
                "Unified CIR PHP",
            ),
        ]

        result = []
        for lang, name, exts, parser_str in languages_metadata:
            parser = cls._parsers.get(lang)
            if parser and parser.is_available():
                status = PipelineStatus.AVAILABLE
            elif parser:
                status = PipelineStatus.IN_DEVELOPMENT
            else:
                status = PipelineStatus.PLANNED

            result.append(
                LanguageInfo(
                    id=lang,
                    display_name=name,
                    extensions=exts,
                    ast_parser=parser_str,
                    status=status,
                )
            )
        return result


# Initialize registry on import
ParserRegistry.initialize()
