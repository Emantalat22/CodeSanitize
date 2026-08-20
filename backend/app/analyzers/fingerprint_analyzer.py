"""Identifier-independent structural AST fingerprinting system."""

import ast
import hashlib
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    FindingCategory,
    FindingSeverity,
    StructuralFingerprint,
    StructuralMetrics,
    SupportedLanguage,
)


class StructuralSkeletonVisitor(ast.NodeVisitor):
    """Normalizes AST into an identifier-independent node type sequence and structural vector."""

    def __init__(self):
        self.node_sequence: List[str] = []
        self.feature_vector: List[int] = [0] * 12

    def generic_visit(self, node: ast.AST):
        node_type = type(node).__name__
        self.node_sequence.append(node_type)

        # Update feature vector
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.feature_vector[0] += 1
        elif isinstance(node, ast.ClassDef):
            self.feature_vector[1] += 1
        elif isinstance(node, (ast.If, ast.IfExp)):
            self.feature_vector[2] += 1
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            self.feature_vector[3] += 1
        elif isinstance(node, ast.While):
            self.feature_vector[4] += 1
        elif isinstance(node, (ast.Try, ast.ExceptHandler)):
            self.feature_vector[5] += 1
        elif isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
            self.feature_vector[6] += 1
        elif isinstance(node, (ast.BinOp, ast.UnaryOp, ast.Compare)):
            self.feature_vector[7] += 1
        elif isinstance(node, (ast.Call,)):
            self.feature_vector[8] += 1
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            self.feature_vector[9] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            self.feature_vector[10] += 1
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            self.feature_vector[11] += 1

        super().generic_visit(node)


class FingerprintAnalyzer(BaseAnalyzer):
    """Extracts identifier-agnostic structural AST fingerprints and topological vectors."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-FPRNT-01"

    @property
    def name(self) -> str:
        return "Structural Fingerprint Analyzer"

    @property
    def description(self) -> str:
        return "Generates identifier-independent AST node sequence fingerprints and topological vectors."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    @classmethod
    def generate_fingerprint(cls, ast_tree: Optional[ast.AST]) -> StructuralFingerprint:
        """Generate canonical structural fingerprint from AST."""
        if ast_tree is None:
            empty_hash = hashlib.sha256(b"empty_ast").hexdigest()
            return StructuralFingerprint(
                ast_node_hash=empty_hash,
                control_flow_fingerprint=empty_hash[:16],
                structure_vector=[0] * 12,
                normalized_skeleton="Empty",
            )

        visitor = StructuralSkeletonVisitor()
        visitor.visit(ast_tree)

        skeleton_str = "->".join(visitor.node_sequence)
        node_hash = hashlib.sha256(skeleton_str.encode("utf-8")).hexdigest()

        cf_str = f"branches:{visitor.feature_vector[2]},loops:{visitor.feature_vector[3]+visitor.feature_vector[4]},exceptions:{visitor.feature_vector[5]}"
        cf_hash = hashlib.sha256(cf_str.encode("utf-8")).hexdigest()[:16]

        return StructuralFingerprint(
            ast_node_hash=node_hash,
            control_flow_fingerprint=cf_hash,
            structure_vector=visitor.feature_vector,
            normalized_skeleton=skeleton_str[:200] + ("..." if len(skeleton_str) > 200 else ""),
        )

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

        fp = self.generate_fingerprint(ast_tree)

        findings.append(
            AnalysisFinding(
                id="FPRNT-AST-HASH-01",
                category=FindingCategory.STRUCTURE,
                severity=FindingSeverity.INFO,
                title="AST Structural Fingerprint Generated",
                description=f"Computed identifier-independent AST topology hash: {fp.ast_node_hash[:12]}...",
                evidence=f"Skeleton: {fp.normalized_skeleton[:80]}",
                recommendation="Structural fingerprints enable topology-based similarity and refactoring clustering.",
            )
        )

        return findings
