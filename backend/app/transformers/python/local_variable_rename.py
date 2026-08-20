"""Safe scope-aware local variable normalization rule for Python with Identifier Intelligence."""

import ast
import builtins
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule
from app.transformers.python.identifier_intelligence import (
    GENERIC_TO_HUMAN,
    IdentifierIntelligence,
)



# Complete set of Python built-in names that must NEVER be renamed
PYTHON_BUILTINS: Set[str] = set(dir(builtins))

# Dynamic reflection functions that invalidate static scoping safety
DYNAMIC_SCOPE_FUNCS: Set[str] = {
    "locals",
    "globals",
    "vars",
    "dir",
    "eval",
    "exec",
    "getattr",
    "setattr",
    "hasattr",
    "delattr",
}


class ScopeSafetyChecker(ast.NodeVisitor):
    """Inspects a function body for constructs that make variable renaming unsafe."""

    def __init__(self):
        self.is_safe = True
        self.unsafe_reason = ""
        self.has_global_or_nonlocal = False
        self.dynamic_calls_detected = False

    def visit_Global(self, node: ast.Global):
        self.is_safe = False
        self.has_global_or_nonlocal = True
        self.unsafe_reason = "Contains 'global' statement"
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self.is_safe = False
        self.has_global_or_nonlocal = True
        self.unsafe_reason = "Contains 'nonlocal' statement"
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in DYNAMIC_SCOPE_FUNCS:
            self.is_safe = False
            self.dynamic_calls_detected = True
            self.unsafe_reason = f"Calls dynamic reflection function '{node.func.id}()'"
        self.generic_visit(node)


class LocalVariableCollector(ast.NodeVisitor):
    """Collects parameter names, assigned local variables and their RHS expression nodes."""

    def __init__(self):
        self.parameters: Set[str] = set()
        self.assigned_locals_order: List[str] = []
        self.assigned_locals_set: Set[str] = set()
        self.assigned_nodes: Dict[str, ast.AST] = {}
        self.free_or_global_reads: Set[str] = set()
        self.attribute_names: Set[str] = set()
        self.defined_callables: Set[str] = set()

    def _add_local(self, name: str, node: Optional[ast.AST] = None):
        if name not in self.assigned_locals_set:
            self.assigned_locals_set.add(name)
            self.assigned_locals_order.append(name)
            if node is not None and name not in self.assigned_nodes:
                self.assigned_nodes[name] = node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self.parameters:
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                self.parameters.add(arg.arg)
            if node.args.vararg:
                self.parameters.add(node.args.vararg.arg)
            if node.args.kwarg:
                self.parameters.add(node.args.kwarg.arg)
            self.defined_callables.add(node.name)
            for stmt in node.body:
                self.visit(stmt)
        else:
            self.defined_callables.add(node.name)
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if not self.parameters:
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                self.parameters.add(arg.arg)
            if node.args.vararg:
                self.parameters.add(node.args.vararg.arg)
            if node.args.kwarg:
                self.parameters.add(node.args.kwarg.arg)
            self.defined_callables.add(node.name)
            for stmt in node.body:
                self.visit(stmt)
        else:
            self.defined_callables.add(node.name)
            self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._add_local(target.id, node.value)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._add_local(elt.id, node.value)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self._add_local(node.target.id, node.value)
        if node.value:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            self._add_local(node.target.id, node.value)
        self.visit(node.value)

    def visit_For(self, node: ast.For):
        if isinstance(node.target, ast.Name):
            self._add_local(node.target.id, node.iter)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        if isinstance(node.target, ast.Name):
            self._add_local(node.target.id, node.iter)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self._add_local(node.id)
        elif isinstance(node.ctx, ast.Load):
            if node.id not in self.assigned_locals_set and node.id not in self.parameters:
                self.free_or_global_reads.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.attribute_names.add(node.attr)
        self.visit(node.value)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            imported_name = alias.asname or alias.name.split(".")[0]
            self.free_or_global_reads.add(imported_name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            imported_name = alias.asname or alias.name
            self.free_or_global_reads.add(imported_name)


class ScopeRenamer(ast.NodeTransformer):
    """Safely replaces matching Name nodes within a function body."""

    def __init__(self, rename_map: Dict[str, str]):
        self.rename_map = rename_map

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.rename_map:
            return ast.copy_location(
                ast.Name(id=self.rename_map[node.id], ctx=node.ctx),
                node,
            )
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Do NOT rename nested function names
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        node.value = self.visit(node.value)
        return node


class SafeLocalVariableRenameRule(BaseTransformationRule):
    """Safely normalizes function-local variables using Identifier Intelligence."""

    @property
    def rule_id(self) -> str:
        return "PY-SAFE-LOCAL-RENAME-01"

    @property
    def name(self) -> str:
        return "Human Identifier Normalization"

    @property
    def description(self) -> str:
        return (
            "Replaces generic AI-style variable names (e.g. result_data, temp_area) with "
            "meaningful, domain-appropriate human identifiers without machine numbers."
        )

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        return TransformationSafetyLevel.SAFE_STRUCTURAL

    @property
    def default_enabled(self) -> bool:
        return True

    def _is_generic_or_ai_name(self, name: str) -> bool:
        """Check if variable name possesses AI-style or generic traits."""
        lower = name.lower()
        if lower.startswith("_norm_") or "_var_" in lower:
            return True
        if lower in GENERIC_TO_HUMAN:
            return True
        if lower.startswith("temp_") or lower.startswith("tmp_") or lower.startswith("result_") or lower.startswith("res_") or lower.startswith("calc_") or lower.startswith("temporary_") or lower.startswith("calculated_"):
            return True
        if lower in (
            "temp", "result", "data", "data_list", "data_dict", "my_list", "my_dict",
            "single_val", "single_element", "val_1", "val_2", "var_1", "var_2",
            "item_1", "item_2", "item_list", "temp_value", "temp_variable", "result_data",
            "output_value", "output_val", "processed_data", "processed_output", "final_result", "calc_result"
        ):
            return True
        return False




    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code.strip():
            return False, "Code is empty."

        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
        except Exception as e:
            return False, f"Syntax parsing failed: {str(e)}"

        eligible_functions = 0
        unsafe_functions = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                checker = ScopeSafetyChecker()
                checker.visit(node)
                if not checker.is_safe:
                    unsafe_functions += 1
                    continue

                collector = LocalVariableCollector()
                collector.visit(node)

                protected = (
                    collector.parameters
                    | collector.free_or_global_reads
                    | collector.defined_callables
                    | PYTHON_BUILTINS
                )
                candidate_locals = [
                    name
                    for name in collector.assigned_locals_order
                    if name not in protected
                    and not (name.startswith("__") and name.endswith("__"))
                    and self._is_generic_or_ai_name(name)
                ]

                if candidate_locals:
                    eligible_functions += 1

        if eligible_functions > 0:
            return True, f"Found {eligible_functions} function(s) with generic AI variables eligible for human normalization."

        if unsafe_functions > 0:
            return (
                False,
                f"Skipped {unsafe_functions} function(s) containing dynamic reflection (locals/globals) or global/nonlocal state.",
            )

        return False, "No generic AI identifiers requiring human normalization."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
        except Exception as e:
            return code, ast_tree, f"AST parsing error: {str(e)}", 0

        total_renamed_count = 0
        renamed_functions: List[str] = []

        for node in tree.body:
            functions_to_check: List[Tuple[Any, Optional[str]]] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions_to_check.append((node, None))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions_to_check.append((item, node.name))

            for func_node, class_name in functions_to_check:
                checker = ScopeSafetyChecker()
                checker.visit(func_node)
                if not checker.is_safe:
                    continue

                collector = LocalVariableCollector()
                collector.visit(func_node)

                protected = (
                    collector.parameters
                    | collector.free_or_global_reads
                    | collector.defined_callables
                    | PYTHON_BUILTINS
                )
                candidates = [
                    name
                    for name in collector.assigned_locals_order
                    if name not in protected
                    and not (name.startswith("__") and name.endswith("__"))
                    and self._is_generic_or_ai_name(name)
                ]

                if not candidates:
                    continue

                rename_map: Dict[str, str] = {}
                used_in_scope = (
                    set(collector.parameters)
                    | set(collector.free_or_global_reads)
                    | set(collector.assigned_locals_set)
                    | PYTHON_BUILTINS
                )

                for old_name in candidates:
                    assigned_ast = collector.assigned_nodes.get(old_name)
                    # Infer meaningful human identifier
                    inferred_name = IdentifierIntelligence.infer_name(
                        current_name=old_name,
                        assigned_node=assigned_ast,
                        enclosing_func_name=func_node.name,
                        used_names=used_in_scope,
                    )

                    if inferred_name != old_name:
                        rename_map[old_name] = inferred_name
                        used_in_scope.add(inferred_name)

                if rename_map:
                    renamer = ScopeRenamer(rename_map)
                    for idx, stmt in enumerate(func_node.body):
                        func_node.body[idx] = renamer.visit(stmt)

                    total_renamed_count += len(rename_map)
                    func_label = f"{class_name}.{func_node.name}" if class_name else func_node.name
                    renamed_functions.append(f"{func_label} ({len(rename_map)} identifiers)")

        if total_renamed_count == 0:
            return code, tree, "No generic AI identifiers required modification.", 0

        try:
            ast.fix_missing_locations(tree)
            transformed_code = ast.unparse(tree)
            # Preserve leading developer header comments (License, Copyright, TODO, shebangs)
            preserved_headers = []
            for line in code.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    lower = stripped.lstrip("#/ *").strip().lower()
                    if any(lower.startswith(p) for p in ("!", "license", "copyright", "todo", "fixme", "note", "type:")):
                        preserved_headers.append(line)
                        continue
                elif not stripped and preserved_headers:
                    preserved_headers.append(line)
                    continue
                break
            
            if preserved_headers:
                header_block = "\n".join(preserved_headers).rstrip() + "\n\n"
                transformed_code = header_block + transformed_code

            if code.endswith("\n") and not transformed_code.endswith("\n"):
                transformed_code += "\n"
            details = f"Normalized {total_renamed_count} AI identifiers into meaningful human names across: {', '.join(renamed_functions)}."
            return transformed_code, tree, details, total_renamed_count

        except Exception as e:
            return code, ast_tree, f"AST unparsing error: {str(e)}", 0
