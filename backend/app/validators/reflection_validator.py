"""Reflection and dynamic evaluation safeguard validator for Python."""

import ast
from typing import Any, Dict, List, Optional, Set
from app.models.schemas import ValidationCheckResult, ValidationRiskFlag, ValidationVerdict
from app.validators.base import BaseValidatorStage

REFLECTION_FUNCTIONS = {
    "locals",
    "globals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "__import__",
}

EVAL_EXEC_FUNCTIONS = {
    "eval",
    "exec",
    "compile",
}

REFLECTION_MODULES = {
    "inspect",
    "importlib",
    "ctypes",
}


class ReflectionFeatureScanner(ast.NodeVisitor):
    """Detects dangerous reflection, dynamic evaluation, and introspection features in AST."""

    def __init__(self):
        self.reflection_calls: Set[str] = set()
        self.eval_exec_calls: Set[str] = set()
        self.dynamic_attr_accesses: Set[str] = set()
        self.reflection_modules: Set[str] = set()
        self.risk_flags: Set[ValidationRiskFlag] = set()

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in REFLECTION_FUNCTIONS:
                self.reflection_calls.add(node.func.id)
                self.risk_flags.add(ValidationRiskFlag.REFLECTION_DETECTED)
            elif node.func.id in EVAL_EXEC_FUNCTIONS:
                self.eval_exec_calls.add(node.func.id)
                self.risk_flags.add(ValidationRiskFlag.EVAL_EXEC_DETECTED)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in REFLECTION_MODULES:
                    self.reflection_modules.add(node.func.value.id)
                    self.risk_flags.add(ValidationRiskFlag.REFLECTION_DETECTED)
                if node.func.attr in ("getattr", "setattr", "delattr", "hasattr"):
                    self.reflection_calls.add(node.func.attr)
                    self.risk_flags.add(ValidationRiskFlag.DYNAMIC_ATTRIBUTE_ACCESS)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr == "__dict__":
            self.reflection_calls.add("__dict__")
            self.risk_flags.add(ValidationRiskFlag.REFLECTION_DETECTED)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in REFLECTION_MODULES:
                self.reflection_modules.add(alias.name)
                self.risk_flags.add(ValidationRiskFlag.REFLECTION_DETECTED)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module in REFLECTION_MODULES:
            self.reflection_modules.add(node.module or "")
            self.risk_flags.add(ValidationRiskFlag.REFLECTION_DETECTED)
        self.generic_visit(node)


class ReflectionSafeguardValidator(BaseValidatorStage):
    """Detects reflective code, introspection, and dynamic code evaluation constructs."""

    @property
    def name(self) -> str:
        return "Reflection & Dynamic Eval Safeguards"

    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST],
        trans_ast: Optional[ast.AST],
        rule_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationCheckResult:
        tree = trans_ast or (ast.parse(trans_code) if trans_code.strip() else None)
        if tree is None:
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.PASSED,
                details="Empty code - no reflection detected.",
            )

        scanner = ReflectionFeatureScanner()
        scanner.visit(tree)

        reasons: List[str] = []
        if scanner.eval_exec_calls:
            reasons.append(f"Dynamic code evaluation detected: {', '.join(scanner.eval_exec_calls)}()")
        if scanner.reflection_calls:
            reasons.append(f"Dynamic scope/attribute reflection detected: {', '.join(scanner.reflection_calls)}")
        if scanner.reflection_modules:
            reasons.append(f"Introspection module(s) imported: {', '.join(scanner.reflection_modules)}")

        if reasons:
            # Reflection patterns introduce ambiguity in static variable scopes
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.WARNING,
                details=f"Dynamic reflection detected: {'; '.join(reasons)}",
                context={
                    "risk_flags": [f.value for f in scanner.risk_flags],
                    "reflection_calls": list(scanner.reflection_calls),
                    "eval_exec_calls": list(scanner.eval_exec_calls),
                },
            )

        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details="No unsafe dynamic reflection, eval/exec, or scope introspection detected.",
        )
