"""Advanced AST Structural Normalization and Pattern Simplification Rule for Python.

Eliminates AI-generated structural fingerprints:
1. Multi-step dictionary accumulation with intermediate variables -> Direct inline dictionary return
   Example:
       result = {}
       value_a = calculate_a()
       value_b = calculate_b()
       result["a"] = value_a
       result["b"] = value_b
       return result
   Becomes:
       return {
           "a": calculate_a(),
           "b": calculate_b()
       }

2. Redundant single-use return variables:
   Example:
       calculated_output = compute(x, y)
       return calculated_output
   Becomes:
       return compute(x, y)

3. Redundant intermediate variable inlining in simple sequential expressions.
"""

import ast
import copy
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule


class NameUsageCounter(ast.NodeVisitor):
    """Counts reads/loads of specific variable names in an AST subtree."""

    def __init__(self):
        self.load_counts: Dict[str, int] = {}
        self.store_counts: Dict[str, int] = {}

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.load_counts[node.id] = self.load_counts.get(node.id, 0) + 1
        elif isinstance(node.ctx, ast.Store):
            self.store_counts[node.id] = self.store_counts.get(node.id, 0) + 1
        self.generic_visit(node)


class StructuralASTOptimizer(ast.NodeTransformer):
    """Applies semantics-preserving structural AST humanizations."""

    def __init__(self):
        self.structural_changes_count = 0
        self.redundant_logic_removed_count = 0
        self.explanations: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        node.body = self._optimize_statement_block(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        self.generic_visit(node)
        node.body = self._optimize_statement_block(node.body)
        return node

    def _optimize_statement_block(self, statements: List[ast.stmt]) -> List[ast.stmt]:
        """Apply structural passes on statement list."""
        current_stmts = statements

        # Pass 1: Dictionary construction & intermediate variable return inlining
        current_stmts, p1_changes = self._pass_dict_return_inlining(current_stmts)
        self.structural_changes_count += p1_changes

        # Pass 2: Subscript assignment inlining (temp_area = math.pi * r**2; dict["area"] = temp_area -> dict["area"] = math.pi * r**2)
        current_stmts, p2_changes = self._pass_subscript_assign_inlining(current_stmts)
        self.structural_changes_count += p2_changes

        # Pass 3: Boolean condition simplification (if cond: return True else: return False -> return cond)
        current_stmts, p3_changes = self._pass_boolean_simplification(current_stmts)
        self.redundant_logic_removed_count += p3_changes
        self.structural_changes_count += p3_changes

        # Pass 4: Unnecessary else block flattening after terminating returns
        current_stmts, p4_changes = self._pass_unnecessary_else(current_stmts)
        self.redundant_logic_removed_count += p4_changes

        # Pass 5: Nested single-if flattening (if a: if b: -> if a and b:)
        current_stmts, p5_changes = self._pass_nested_if_flattening(current_stmts)
        self.structural_changes_count += p5_changes

        # Pass 6: Redundant single-use return variable elimination (var = expr; return var -> return expr)
        current_stmts, p6_changes = self._pass_redundant_return_inlining(current_stmts)
        self.redundant_logic_removed_count += p6_changes

        return current_stmts

    def _pass_boolean_simplification(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:
        """Simplifies verbose if-condition return boolean structures."""
        new_stmts = []
        changes = 0

        for stmt in statements:
            if (
                isinstance(stmt, ast.If)
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], ast.Return)
                and isinstance(stmt.body[0].value, ast.Constant)
                and isinstance(stmt.body[0].value.value, bool)
                and len(stmt.orelse) == 1
                and isinstance(stmt.orelse[0], ast.Return)
                and isinstance(stmt.orelse[0].value, ast.Constant)
                and isinstance(stmt.orelse[0].value.value, bool)
            ):
                if_val = stmt.body[0].value.value
                else_val = stmt.orelse[0].value.value

                if if_val is True and else_val is False:
                    new_ret = ast.copy_location(ast.Return(value=stmt.test), stmt)
                    new_stmts.append(new_ret)
                    changes += 1
                    self.explanations.append("Simplified verbose if/else boolean return into direct return condition.")
                    continue
                elif if_val is False and else_val is True:
                    not_expr = ast.UnaryOp(op=ast.Not(), operand=stmt.test)
                    new_ret = ast.copy_location(ast.Return(value=not_expr), stmt)
                    new_stmts.append(new_ret)
                    changes += 1
                    self.explanations.append("Simplified verbose inverted boolean return into 'return not condition'.")
                    continue

            new_stmts.append(stmt)

        return new_stmts, changes

    def _pass_unnecessary_else(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:
        """Flattens unnecessary else blocks when if-branch terminates with a return."""
        new_stmts = []
        changes = 0

        for stmt in statements:
            if (
                isinstance(stmt, ast.If)
                and stmt.orelse
                and stmt.body
                and isinstance(stmt.body[-1], (ast.Return, ast.Raise))
            ):
                else_body = stmt.orelse
                stmt.orelse = []
                new_stmts.append(stmt)
                new_stmts.extend(else_body)
                changes += 1
                self.explanations.append("Flattened unnecessary else block following terminating return.")
            else:
                new_stmts.append(stmt)

        return new_stmts, changes

    def _pass_nested_if_flattening(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:
        """Combines nested single-child if-conditions: if a: if b: -> if a and b:"""
        new_stmts = []
        changes = 0

        for stmt in statements:
            if (
                isinstance(stmt, ast.If)
                and not stmt.orelse
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], ast.If)
                and not stmt.body[0].orelse
            ):
                inner_if = stmt.body[0]
                combined_test = ast.BoolOp(
                    op=ast.And(),
                    values=[stmt.test, inner_if.test],
                )
                combined_if = ast.copy_location(
                    ast.If(test=combined_test, body=inner_if.body, orelse=[]),
                    stmt,
                )
                new_stmts.append(combined_if)
                changes += 1
                self.explanations.append("Combined nested single-child if-conditions into composite boolean condition.")
            else:
                new_stmts.append(stmt)

        return new_stmts, changes


    def _pass_subscript_assign_inlining(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:
        """Inlines single-use temporary variables into subscript assignments."""
        new_stmts = []
        i = 0
        n = len(statements)
        changes = 0

        full_block = ast.Module(body=statements, type_ignores=[])
        usage = NameUsageCounter()
        usage.visit(full_block)

        available_inlines: Dict[str, ast.AST] = {}

        while i < n:
            stmt = statements[i]
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
            ):
                var_name = stmt.targets[0].id
                if usage.load_counts.get(var_name, 0) == 1 and (
                    var_name.startswith("temp_")
                    or var_name.startswith("tmp_")
                    or var_name.startswith("val_")
                    or var_name in ("temp", "val", "value", "item_1", "item_2")
                ):
                    subscript_found = False
                    for peek_idx in range(i + 1, min(i + 10, n)):
                        peek_stmt = statements[peek_idx]
                        if (
                            isinstance(peek_stmt, ast.Assign)
                            and len(peek_stmt.targets) == 1
                            and isinstance(peek_stmt.targets[0], ast.Subscript)
                            and isinstance(peek_stmt.value, ast.Name)
                            and peek_stmt.value.id == var_name
                        ):
                            subscript_found = True
                            break
                        if not isinstance(peek_stmt, ast.Assign):
                            break

                    if subscript_found:
                        available_inlines[var_name] = stmt.value
                        i += 1
                        continue

            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Subscript)
                and isinstance(stmt.value, ast.Name)
                and stmt.value.id in available_inlines
            ):
                inlined_value = available_inlines.pop(stmt.value.id)
                new_stmt = ast.copy_location(
                    ast.Assign(targets=stmt.targets, value=inlined_value),
                    stmt,
                )
                new_stmts.append(new_stmt)
                changes += 1
                self.explanations.append(
                    f"Inlined temporary variable '{stmt.value.id}' directly into dictionary subscript assignment."
                )
                i += 1
                continue

            new_stmts.append(stmt)
            i += 1

        return new_stmts, changes

    def _pass_dict_return_inlining(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:

        """Inlines intermediate variables and dictionary assignments into a single inline dictionary return."""
        new_stmts = []
        i = 0
        n = len(statements)
        changes = 0

        # Global load counter for the whole block to ensure inlined variables are not read elsewhere
        full_block = ast.Module(body=statements, type_ignores=[])
        usage = NameUsageCounter()
        usage.visit(full_block)

        while i < n:
            stmt = statements[i]
            matched = False

            # Check for pattern:
            # 1. (Optional) intermediate assigns: var_1 = expr1, var_2 = expr2
            # 2. dict_name = {}
            # 3. (Or intermediate assigns mixed with) dict_name[k] = val
            # 4. return dict_name
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                dict_var = stmt.targets[0].id
                if isinstance(stmt.value, ast.Dict) and len(stmt.value.keys) == 0:
                    # Found `dict_var = {}` at index i
                    # Collect preceding local intermediate variables within same block if they were defined right before
                    local_inlines: Dict[str, ast.AST] = {}
                    preceding_idx = i - 1
                    consumed_preceding = 0

                    while preceding_idx >= 0:
                        prec_stmt = statements[preceding_idx]
                        if isinstance(prec_stmt, ast.Assign) and len(prec_stmt.targets) == 1 and isinstance(prec_stmt.targets[0], ast.Name):
                            p_name = prec_stmt.targets[0].id
                            # Check if p_name is only used once in the following dict population
                            if usage.load_counts.get(p_name, 0) == 1:
                                local_inlines[p_name] = prec_stmt.value
                                consumed_preceding += 1
                                preceding_idx -= 1
                                continue
                        break

                    # Look ahead for dict_var[k] = expr or var_k = expr; dict_var[k] = var_k; ... return dict_var
                    j = i + 1
                    dict_entries: List[Tuple[ast.AST, ast.AST]] = []
                    retained_stmts: List[ast.stmt] = []
                    valid = True

                    while j < n:
                        next_stmt = statements[j]
                        # Subscript assign: dict_var[k] = expr
                        if (
                            isinstance(next_stmt, ast.Assign)
                            and len(next_stmt.targets) == 1
                            and isinstance(next_stmt.targets[0], ast.Subscript)
                            and isinstance(next_stmt.targets[0].value, ast.Name)
                            and next_stmt.targets[0].value.id == dict_var
                        ):
                            key_node = next_stmt.targets[0].slice
                            val_node = next_stmt.value
                            # If val_node is a Name in local_inlines, substitute directly!
                            if isinstance(val_node, ast.Name) and val_node.id in local_inlines:
                                val_node = local_inlines[val_node.id]
                            dict_entries.append((key_node, val_node))
                            j += 1
                        # Intermediate variable assigned and then used: val_x = expr
                        elif isinstance(next_stmt, ast.Assign) and len(next_stmt.targets) == 1 and isinstance(next_stmt.targets[0], ast.Name):
                            t_name = next_stmt.targets[0].id
                            if usage.load_counts.get(t_name, 0) == 1:
                                local_inlines[t_name] = next_stmt.value
                            else:
                                retained_stmts.append(next_stmt)
                            j += 1
                        elif (
                            isinstance(next_stmt, ast.Return)
                            and isinstance(next_stmt.value, ast.Name)
                            and next_stmt.value.id == dict_var
                        ):
                            # Reached `return dict_var`
                            if dict_entries:
                                # Rewind new_stmts if we consumed preceding assignments
                                if consumed_preceding > 0:
                                    new_stmts = new_stmts[:-consumed_preceding] if len(new_stmts) >= consumed_preceding else []

                                for ret_s in retained_stmts:
                                    new_stmts.append(ret_s)

                                inline_dict = ast.Dict(
                                    keys=[k for k, v in dict_entries],
                                    values=[v for k, v in dict_entries],
                                )
                                return_stmt = ast.copy_location(
                                    ast.Return(value=inline_dict),
                                    next_stmt,
                                )
                                new_stmts.append(return_stmt)
                                changes += 1
                                self.explanations.append(
                                    f"Simplified multi-step dictionary construction into clean inline return with {len(dict_entries)} fields."
                                )
                                i = j + 1
                                matched = True
                                break
                            else:
                                valid = False
                                break
                        else:
                            valid = False
                            break


                    if matched:
                        continue

            if not matched:
                new_stmts.append(stmt)
                i += 1

        return new_stmts, changes

    def _pass_redundant_return_inlining(self, statements: List[ast.stmt]) -> Tuple[List[ast.stmt], int]:
        """Eliminates redundant `var = expr; return var` sequences into direct `return expr`."""
        new_stmts = []
        i = 0
        n = len(statements)
        changes = 0

        full_block = ast.Module(body=statements, type_ignores=[])
        usage = NameUsageCounter()
        usage.visit(full_block)

        while i < n:
            stmt = statements[i]
            if i + 1 < n:
                next_stmt = statements[i + 1]
                # Pattern: var = expr; return var
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(next_stmt, ast.Return)
                    and isinstance(next_stmt.value, ast.Name)
                ):
                    var_name = stmt.targets[0].id
                    ret_name = next_stmt.value.id
                    if var_name == ret_name and usage.load_counts.get(var_name, 0) == 1:
                        # Direct return expr
                        return_stmt = ast.copy_location(
                            ast.Return(value=stmt.value),
                            next_stmt,
                        )
                        new_stmts.append(return_stmt)
                        changes += 1
                        self.explanations.append(
                            f"Inlined single-use return variable '{var_name}' into direct return expression."
                        )
                        i += 2
                        continue

            new_stmts.append(stmt)
            i += 1

        return new_stmts, changes


class PythonCodeSimplificationRule(BaseTransformationRule):
    """Transforms AI-generated boilerplate structures into clean, idiomatic human-written code."""

    @property
    def rule_id(self) -> str:
        return "PY-STRUCT-SIMPLIFY-01"

    @property
    def name(self) -> str:
        return "AST Structural Normalization & Simplification"

    @property
    def description(self) -> str:
        return (
            "Simplifies textbook multi-step dictionary/list constructions, inlines single-use "
            "temporary variables, and removes redundant intermediate logic while preserving 100% semantics."
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

    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code.strip():
            return False, "Code is empty."

        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
        except Exception as e:
            return False, f"Syntax parsing failed: {str(e)}"

        optimizer = StructuralASTOptimizer()
        test_tree = copy.deepcopy(tree)
        optimizer.visit(test_tree)

        total_mods = optimizer.structural_changes_count + optimizer.redundant_logic_removed_count
        if total_mods > 0:
            return True, f"Found {total_mods} structural pattern(s) eligible for human developer simplification."

        return False, "No verbose structural patterns requiring simplification."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        try:
            tree = ast_tree if ast_tree is not None else ast.parse(code)
        except Exception as e:
            return code, ast_tree, f"AST parsing error: {str(e)}", 0

        optimizer = StructuralASTOptimizer()
        modified_tree = optimizer.visit(tree)

        total_mods = optimizer.structural_changes_count + optimizer.redundant_logic_removed_count
        if total_mods == 0:
            return code, tree, "No structural modifications performed.", 0

        try:
            ast.fix_missing_locations(modified_tree)
            transformed_code = ast.unparse(modified_tree)
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
            details = (
                f"Applied structural humanization: {optimizer.structural_changes_count} structure(s) simplified, "
                f"{optimizer.redundant_logic_removed_count} redundant return variable(s) inlined."
            )
            return transformed_code, modified_tree, details, total_mods

        except Exception as e:
            return code, ast_tree, f"AST unparsing error: {str(e)}", 0
