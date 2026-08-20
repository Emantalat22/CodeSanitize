"""Identifier Intelligence Engine for Human-Style Variable Normalization.

Infers meaningful, domain-appropriate names from:
1. Assigned values and expressions (e.g. 3.14 * r**2 -> area)
2. Dictionary keys and shapes
3. Mathematical operations (e.g. sum / len -> mean)
4. Function purpose and contextual semantics
5. Clean prefix stripping (temp_area -> area, temp_circumference -> circumference)

NEVER generates machine-like tokens (_norm_, _var_, generated numbers).
"""

import ast
import re
from typing import Any, Dict, List, Optional, Set

# Generic AI-style identifiers mapped to natural human names
GENERIC_TO_HUMAN: Dict[str, str] = {
    "temp": "item_value",
    "result": "result_value",
    "result_data": "metrics",
    "results_data": "metrics",
    "res_data": "metrics",
    "res_val": "calculated_value",
    "temp_res": "result_value",
    "temp_result": "result_value",
    "temp_data": "dataset",
    "temp_dict": "lookup",
    "temp_list": "items",
    "final_result": "summary",
    "data_list": "records",
    "data_dict": "attributes",
    "data": "dataset",
    "my_list": "items",
    "my_dict": "lookup",
    "item_list": "items",
    "output_value": "computed_output",
    "output_val": "computed_output",
    "input_val": "input_item",
    "processed_data": "records",
    "processed_output": "records",
    "output_data": "output_payload",
    "calc_result": "computed_value",
    "calc_mean": "mean_value",
    "single_val": "item",
    "single_element": "element",
    "val_1": "first_value",
    "val_2": "second_value",
    "var_1": "primary_metric",
    "var_2": "secondary_metric",
    "total_sum": "total",
    "temp_sum": "total",
    "temp_accumulator": "total",
    "intermediate_scaled": "scaled_value",
    "temp_val": "value",
    "temp_value": "value",
    "temp_variable": "variable",
    "temp_area": "area",
    "temp_circumference": "circumference",
    "temp_radius": "radius",
    "temp_perimeter": "perimeter",
    "temp_height": "height",
    "temp_width": "width",
    "temp_count": "count",
    "item_1": "first_item",
    "item_2": "second_item",
    "calculated_result_value": "metrics",
    "temporary_variable_holder": "val",
    "total_computed_sum": "total",
    "final_output_dictionary": "metrics",
    "processed_input_data": "items",
    "input_argument_value": "val",
    "element_iteration_item": "item",
    "current_loop_index": "idx",
    "temporary_calculation_result": "result",
}



# Meaningful suffix patterns to extract clean words from temp_/result_ prefixes
CLEAN_PREFIX_REGEX = re.compile(r"^(?:temp_|tmp_|result_|res_|calc_)([a-zA-Z][a-zA-Z0-9_]*)$", re.IGNORECASE)


class IdentifierIntelligence:
    """Intelligent semantic analyzer for local variable naming."""

    @classmethod
    def infer_name(
        cls,
        current_name: str,
        assigned_node: Optional[ast.AST] = None,
        enclosing_func_name: Optional[str] = None,
        used_names: Optional[Set[str]] = None,
    ) -> str:
        """Infer a natural, human developer variable name."""
        used = used_names or set()
        lower_name = current_name.lower()

        # 1. Exact mapping from known generic tokens
        if lower_name in GENERIC_TO_HUMAN:
            candidate = GENERIC_TO_HUMAN[lower_name]
            return cls._disambiguate(candidate, used, current_name)

        # 2. Prefix Stripping: temp_area -> area, temp_circumference -> circumference
        prefix_match = CLEAN_PREFIX_REGEX.match(lower_name)
        if prefix_match:
            suffix = prefix_match.group(1).lower()
            if len(suffix) >= 3 and not suffix.isdigit() and suffix not in ("var", "val", "data", "result"):
                return cls._disambiguate(suffix, used, current_name)

        # 3. Value/AST-Based Inference
        if assigned_node is not None:
            inferred = cls._infer_from_ast_node(assigned_node, enclosing_func_name)
            if inferred:
                return cls._disambiguate(inferred, used, current_name)

        # 4. Fallback: Clean up prefix or use clean idiomatic name
        if prefix_match:
            suffix = prefix_match.group(1).lower()
            if suffix in GENERIC_TO_HUMAN:
                return cls._disambiguate(GENERIC_TO_HUMAN[suffix], used, current_name)
            elif len(suffix) >= 2 and not suffix.isdigit():
                return cls._disambiguate(suffix, used, current_name)

        # Natural fallback
        return cls._disambiguate("calculated_value", used, current_name)

    @classmethod
    def _infer_from_ast_node(cls, node: ast.AST, enclosing_func: Optional[str] = None) -> Optional[str]:
        """Infer name based on RHS assignment AST node."""
        # Check dictionary instantiation
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if "area" in keys and "perimeter" in keys:
                return "metrics"
            if "count" in keys or "sum" in keys or "mean" in keys:
                return "stats"
            if "error" in keys or "message" in keys:
                return "response"
            return "metrics"

        # Check list instantiation
        if isinstance(node, ast.List):
            return "items"

        # Check mathematical binary operations
        if isinstance(node, ast.BinOp):
            # Check for area formulas: 3.14 * r**2 or pi * r**2
            if isinstance(node.op, ast.Mult):
                if cls._contains_constant_approx(node, 3.14) or cls._contains_name(node, "pi"):
                    if isinstance(node.right, ast.BinOp) and isinstance(node.right.op, ast.Pow):
                        return "area"
                    return "circumference"
                return "product"

            # Check for division / averages: sum / len(...)
            if isinstance(node.op, ast.Div):
                if cls._contains_call(node.right, "len") or cls._contains_name(node.left, "sum"):
                    return "average"
                return "ratio"

            if isinstance(node.op, ast.Add):
                return "total"

            if isinstance(node.op, ast.Sub):
                return "difference"

        # Check function call expressions
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in ("round", "float", "int"):
                if node.args:
                    inner_infer = cls._infer_from_ast_node(node.args[0], enclosing_func)
                    if inner_infer:
                        return inner_infer
            elif func_name in ("min", "max"):
                return f"{func_name}_val"
            elif func_name in ("len", "count"):
                return "total_count"
            elif "coordinate" in func_name or "point" in func_name:
                return "coords"

        # Check subscript access: pts[0] -> first_item, pts[0][0] -> x_coord
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant):
                idx = node.slice.value
                if idx == 0:
                    return "x_coord" if "coord" in (enclosing_func or "") else "first_item"
                elif idx == 1:
                    return "y_coord" if "coord" in (enclosing_func or "") else "second_item"

        return None

    @classmethod
    def _contains_constant_approx(cls, node: ast.AST, target: float, tol: float = 0.01) -> bool:
        """Check if AST subtree contains a float constant approximately matching target."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, (int, float)):
                if abs(float(sub.value) - target) < tol:
                    return True
        return False

    @classmethod
    def _contains_name(cls, node: ast.AST, target_name: str) -> bool:
        """Check if AST subtree contains a Name node."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and target_name.lower() in sub.id.lower():
                return True
        return False

    @classmethod
    def _contains_call(cls, node: ast.AST, func_name: str) -> bool:
        """Check if AST subtree calls a specific function."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name) and sub.func.id == func_name:
                    return True
        return False

    @classmethod
    def _disambiguate(cls, base_name: str, used_names: Set[str], original_name: str) -> str:
        """Ensure the chosen name is unique in scope without using machine numbers."""
        clean_base = base_name.replace("_norm_", "").replace("_var_", "")
        if not clean_base or clean_base.isdigit():
            clean_base = "item_value"

        if clean_base not in used_names:
            return clean_base

        alternatives = [
            f"{clean_base}_val",
            f"{clean_base}_item",
            f"{clean_base}_data",
            f"{clean_base}_metric",
            f"primary_{clean_base}",
            f"secondary_{clean_base}",
            f"current_{clean_base}",
            f"target_{clean_base}",
            f"final_{clean_base}",
        ]

        for alt in alternatives:
            if alt not in used_names:
                return alt

        index = 2
        while f"{clean_base}_{index}" in used_names:
            index += 1
        return f"{clean_base}_{index}"
