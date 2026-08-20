"""AST Structural Validator verifying module-level and statement hierarchy invariants."""

import ast
from typing import Any, Dict, List, Optional, Set
from app.models.schemas import ValidationCheckResult, ValidationVerdict
from app.validators.base import BaseValidatorStage


class StructuralFeatureCollector(ast.NodeVisitor):
    """Gathers structural properties: decorators, async/sync, generators, exception blocks, globals."""

    def __init__(self):
        self.async_functions: Set[str] = set()
        self.sync_functions: Set[str] = set()
        self.generator_functions: Set[str] = set()
        self.decorators: Dict[str, List[str]] = {}
        self.exception_handler_counts: int = 0
        self.global_declarations: Set[str] = set()
        self.nonlocal_declarations: Set[str] = set()
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev = self.current_function
        self.current_function = node.name
        self.sync_functions.add(node.name)
        
        decs = []
        for d in node.decorator_list:
            try:
                decs.append(ast.unparse(d))
            except Exception:
                decs.append(str(d))
        if decs:
            self.decorators[f"func::{node.name}"] = decs

        self.generic_visit(node)
        self.current_function = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        prev = self.current_function
        self.current_function = node.name
        self.async_functions.add(node.name)

        decs = []
        for d in node.decorator_list:
            try:
                decs.append(ast.unparse(d))
            except Exception:
                decs.append(str(d))
        if decs:
            self.decorators[f"func::{node.name}"] = decs

        self.generic_visit(node)
        self.current_function = prev

    def visit_ClassDef(self, node: ast.ClassDef):
        decs = []
        for d in node.decorator_list:
            try:
                decs.append(ast.unparse(d))
            except Exception:
                decs.append(str(d))
        if decs:
            self.decorators[f"class::{node.name}"] = decs
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield):
        if self.current_function:
            self.generator_functions.add(self.current_function)
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom):
        if self.current_function:
            self.generator_functions.add(self.current_function)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.exception_handler_counts += 1
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self.global_declarations.add(name)
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.nonlocal_declarations.add(name)
        self.generic_visit(node)


class AstStructuralValidator(BaseValidatorStage):
    """Verifies structural AST invariants while accommodating approved intentional transformations."""

    @property
    def name(self) -> str:
        return "AST Structural Invariants"

    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST],
        trans_ast: Optional[ast.AST],
        rule_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationCheckResult:
        if orig_ast is None or trans_ast is None:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details="Baseline or candidate AST unavailable for structural comparison.",
            )

        orig_col = StructuralFeatureCollector()
        orig_col.visit(orig_ast)

        trans_col = StructuralFeatureCollector()
        trans_col.visit(trans_ast)

        mismatches: List[str] = []

        # 1. Check Async status
        if orig_col.async_functions != trans_col.async_functions:
            mismatches.append(
                f"Async function status changed (orig: {orig_col.async_functions}, trans: {trans_col.async_functions})"
            )

        # 2. Check Generator status (yield / yield from)
        if orig_col.generator_functions != trans_col.generator_functions:
            mismatches.append(
                f"Generator function status changed (orig: {orig_col.generator_functions}, trans: {trans_col.generator_functions})"
            )

        # 3. Check Decorator preservation
        if orig_col.decorators != trans_col.decorators:
            mismatches.append("Function or class decorators were altered or omitted")

        # 4. Check Exception Handlers
        if orig_col.exception_handler_counts != trans_col.exception_handler_counts:
            mismatches.append(
                f"Exception handler count mutated from {orig_col.exception_handler_counts} to {trans_col.exception_handler_counts}"
            )

        # 5. Check Global / Nonlocal Declarations
        if orig_col.global_declarations != trans_col.global_declarations:
            mismatches.append("Global variable declarations mutated")

        if orig_col.nonlocal_declarations != trans_col.nonlocal_declarations:
            mismatches.append("Nonlocal declarations mutated")

        if mismatches:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Structural invariant violations: {'; '.join(mismatches)}",
                context={"violations": mismatches},
            )

        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details="All structural invariants (async status, generators, decorators, exception handlers, globals) strictly preserved.",
        )
