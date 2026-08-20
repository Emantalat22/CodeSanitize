"""Structural similarity analysis engine comparing AST fingerprints and topological vectors."""

import ast
import math
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.analyzers.fingerprint_analyzer import FingerprintAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    FindingCategory,
    FindingSeverity,
    SimilarityScore,
    StructuralFingerprint,
    StructuralMetrics,
    SupportedLanguage,
)


class SimilarityAnalyzer(BaseAnalyzer):
    """Calculates structural similarity against reference ASTs without making authorship/AI claims."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-SIM-01"

    @property
    def name(self) -> str:
        return "Structural Similarity Analyzer"

    @property
    def description(self) -> str:
        return "Evaluates topological AST similarity and vector distance against reference baselines."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    @classmethod
    def calculate_similarity(
        cls, fp_a: StructuralFingerprint, fp_b: StructuralFingerprint
    ) -> SimilarityScore:
        """Calculate cosine similarity of structural vectors and hash matches."""
        # 1. Exact AST skeleton match
        if fp_a.ast_node_hash == fp_b.ast_node_hash:
            return SimilarityScore(
                score=100.0,
                confidence="high",
                explanation="Identical structural topology and AST node sequence match.",
            )

        # 2. Vector Cosine Similarity
        vec_a = fp_a.structure_vector
        vec_b = fp_b.structure_vector

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return SimilarityScore(
                score=0.0,
                confidence="low",
                explanation="One or both structural vectors are empty.",
            )

        cosine_sim = dot_product / (norm_a * norm_b)
        score = round(max(0.0, min(cosine_sim * 100.0, 100.0)), 1)

        if score >= 90.0:
            explanation = "High structural similarity: statement distributions and control flow topology align closely."
        elif score >= 70.0:
            explanation = "Moderate structural similarity: share similar branching and function distribution patterns."
        else:
            explanation = "Low structural similarity: distinct AST layouts and control topologies."

        return SimilarityScore(score=score, confidence="high", explanation=explanation)

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []

        if ast_tree is None:
            return findings

        # If options contain a comparison AST or reference code
        ref_code = options.get("reference_code")
        if ref_code and isinstance(ref_code, str):
            try:
                ref_tree = ast.parse(ref_code)
                fp_current = FingerprintAnalyzer.generate_fingerprint(ast_tree)
                fp_ref = FingerprintAnalyzer.generate_fingerprint(ref_tree)
                sim = self.calculate_similarity(fp_current, fp_ref)

                findings.append(
                    AnalysisFinding(
                        id="SIM-COMPARE-01",
                        category=FindingCategory.SIMILARITY,
                        severity=FindingSeverity.INFO,
                        title=f"Structural Similarity: {sim.score}%",
                        description=sim.explanation,
                        evidence=f"Similarity Score: {sim.score}/100",
                        recommendation="Structural similarity metrics provide topology comparison without text dependence.",
                    )
                )
            except Exception:
                pass

        return findings
