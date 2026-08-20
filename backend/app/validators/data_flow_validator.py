"""Conservative data-flow and lexical definition-use validator for Python."""

import ast
import builtins
from typing import Any, Dict, List, Optional, Set
from app.models.schemas import ValidationCheckResult, ValidationVerdict
from app.validators.base import BaseValidatorStage

PYTHON_BUILTINS = set(dir(builtins))


class ScopeNode:
    """Represents a lexical scope (module or function)."""

    def __init__(self, name: str, parent: Optional["ScopeNode"] = None):
        self.name = name
        self.parent = parent
        self.parameters: Set[str] = set()
        self.assigned_vars: Set[str] = set()
        self.read_vars: Set[str] = set()
        self.global_vars: Set[str] = set()
        self.nonlocal_vars: Set[str] = set()
        self.children: List["ScopeNode"] = []

    def get_all_visible_symbols(self) -> Set[str]:
        """Collect all symbols visible in this scope, traversing parent scopes up to module."""
        symbols = (
            set(self.parameters)
            | set(self.assigned_vars)
            | set(self.global_vars)
            | set(self.nonlocal_vars)
            | PYTHON_BUILTINS
        )
        if self.parent:
            symbols |= self.parent.get_all_visible_symbols()
        return symbols


class HierarchicalScopeBuilder(ast.NodeVisitor):
    """Builds a tree of lexical scopes and records all symbol definitions and usages."""

    def __init__(self):
        self.module_scope = ScopeNode("<module>")
        self.current_scope = self.module_scope
        self.all_function_scopes: Dict[str, ScopeNode] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        scope_name = f"{self.current_scope.name}::{node.name}"
        fn_scope = ScopeNode(scope_name, parent=self.current_scope)
        self.current_scope.children.append(fn_scope)
        self.all_function_scopes[scope_name] = fn_scope

        # Collect parameters
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            fn_scope.parameters.add(arg.arg)
        if node.args.vararg:
            fn_scope.parameters.add(node.args.vararg.arg)
        if node.args.kwarg:
            fn_scope.parameters.add(node.args.kwarg.arg)

        # Enter scope
        prev = self.current_scope
        self.current_scope = fn_scope

        for stmt in node.body:
            self.visit(stmt)

        self.current_scope = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        scope_name = f"{self.current_scope.name}::{node.name}"
        fn_scope = ScopeNode(scope_name, parent=self.current_scope)
        self.current_scope.children.append(fn_scope)
        self.all_function_scopes[scope_name] = fn_scope

        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            fn_scope.parameters.add(arg.arg)
        if node.args.vararg:
            fn_scope.parameters.add(node.args.vararg.arg)
        if node.args.kwarg:
            fn_scope.parameters.add(node.args.kwarg.arg)

        prev = self.current_scope
        self.current_scope = fn_scope

        for stmt in node.body:
            self.visit(stmt)

        self.current_scope = prev

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_scope.assigned_vars.add(node.name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self.current_scope.global_vars.add(name)
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.current_scope.nonlocal_vars.add(name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.current_scope.assigned_vars.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.current_scope.read_vars.add(node.id)
        self.generic_visit(node)


class DataFlowValidator(BaseValidatorStage):
    """Verifies data-flow integrity, lexical scope resolution, and definition-use relationships."""

    @property
    def name(self) -> str:
        return "Data-Flow & Scope Safeguards"

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
                details="Baseline or candidate AST unavailable for data-flow validation.",
            )

        orig_builder = HierarchicalScopeBuilder()
        orig_builder.visit(orig_ast)

        trans_builder = HierarchicalScopeBuilder()
        trans_builder.visit(trans_ast)

        failures: List[str] = []
        warnings: List[str] = []

        for scope_name, trans_scope in trans_builder.all_function_scopes.items():
            orig_scope = orig_builder.all_function_scopes.get(scope_name)
            if not orig_scope:
                continue

            # 1. Parameter Names Invariance
            if orig_scope.parameters != trans_scope.parameters:
                failures.append(
                    f"Scope '{scope_name}' parameters mutated from {orig_scope.parameters} to {trans_scope.parameters}"
                )

            # 2. Check for Undefined Variable Loads (Lexical Scoping Chain)
            visible_symbols = trans_scope.get_all_visible_symbols()

            for read_var in trans_scope.read_vars:
                if read_var not in visible_symbols and not read_var.startswith("__"):
                    # Check if it was present in original scope
                    if read_var not in orig_scope.read_vars and read_var not in orig_scope.get_all_visible_symbols():
                        failures.append(
                            f"Scope '{scope_name}' references undefined variable '{read_var}'"
                        )

            # 3. Check for Accidental Shadowing of Parameter Names
            for assigned_var in trans_scope.assigned_vars:
                if assigned_var in trans_scope.parameters and assigned_var not in orig_scope.assigned_vars:
                    warnings.append(
                        f"Scope '{scope_name}' variable assignment accidentally shadows parameter '{assigned_var}'"
                    )

        if failures:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Data-flow violations detected: {'; '.join(failures)}",
                context={"failures": failures, "warnings": warnings},
            )

        if warnings:
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.WARNING,
                details=f"Data-flow warnings flagged: {'; '.join(warnings)}",
                context={"warnings": warnings},
            )

        func_count = len(orig_builder.all_function_scopes)
        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details=f"Data-flow definition-use chains and lexical scoping verified across {func_count} scope(s).",
        )
