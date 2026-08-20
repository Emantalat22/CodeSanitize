"""Code Style and Formatting Pattern Analyzer for AI Code Provenance."""

import re
from typing import List
from app.models.schemas import SupportedLanguage
from app.provenance.models import ProvenanceSignal, StyleAnalysisResult


class StylePatternAnalyzer:
    """Analyzes stylistic regularities, symmetry, and textbook scaffolding in source code."""

    @classmethod
    def analyze(cls, code: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> StyleAnalysisResult:
        """Perform static style and symmetry analysis."""
        signals: List[ProvenanceSignal] = []
        lines = [l for l in code.splitlines() if l.strip()]

        if not lines:
            return StyleAnalysisResult(uniformity_score=0.0, excessive_regularity=False, signals=[])

        # 1. Check for standard textbook demo test harness at module bottom
        if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', code):
            if re.search(r'print\(["\'](?:Sample|Output|Result|Testing|Computed):?', code):
                signals.append(
                    ProvenanceSignal(
                        signal_type="textbook_demo_harness",
                        severity="low",
                        confidence=0.7,
                        description="Textbook-style demonstration block at module entry point",
                        evidence="if __name__ == '__main__': ... print(...)",
                    )
                )

        # 2. Check for boilerplate generic error handling `except Exception as e: print(f"Error: {e}")`
        generic_excepts = re.findall(r'except\s+Exception\s+as\s+e\s*:\s*\n\s*print\(f?["\'](?:An\s+)?Error(?:\s+occurred)?:', code, re.IGNORECASE)
        if generic_excepts:
            signals.append(
                ProvenanceSignal(
                    signal_type="generic_exception_logging",
                    severity="medium",
                    confidence=0.85,
                    description="Generic boilerplate exception catch with standard print statement",
                    evidence="except Exception as e: print(f'Error: {e}')",
                )
            )

        # 3. Calculate line length variance and uniformity score
        line_lengths = [len(l) for l in lines]
        avg_len = sum(line_lengths) / max(len(line_lengths), 1)
        variance = sum((l - avg_len) ** 2 for l in line_lengths) / max(len(line_lengths), 1)
        std_dev = variance ** 0.5

        # If code has > 10 lines and very tight standard deviation, it suggests templated regularity
        excessive_regularity = False
        if len(lines) >= 12 and std_dev < 8.0:
            excessive_regularity = True
            signals.append(
                ProvenanceSignal(
                    signal_type="excessive_structural_regularity",
                    severity="low",
                    confidence=0.65,
                    description=f"Highly symmetrical line length distribution (σ={round(std_dev, 1)})",
                )
            )

        uniformity_score = round(min(max(100.0 - (std_dev * 2.5), 0.0), 100.0), 1)

        return StyleAnalysisResult(
            uniformity_score=uniformity_score,
            excessive_regularity=excessive_regularity,
            signals=signals,
        )
