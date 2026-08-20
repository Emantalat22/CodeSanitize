"""Identifier Pattern Analyzer for AI Code Provenance."""

import ast
import re
from typing import List, Set
from app.models.schemas import SupportedLanguage
from app.provenance.models import IdentifierAnalysisResult, ProvenanceSignal

GENERIC_VARIABLE_NAMES = {
    "temp_value",
    "temp_variable",
    "temp_val",
    "result_data",
    "processed_output",
    "final_result",
    "output_list",
    "data_item",
    "current_item",
    "res_val",
    "input_data",
    "output_dict",
    "temp_list",
    "user_input",
    "item_list",
    "temp_result",
    "return_value",
    "my_list",
    "my_dict",
    "data_obj",
    "item_1",
    "item_2",
    "data",
    "temp_area",
    "temp_circumference",
}



class IdentifierPatternAnalyzer:
    """Detects formulaic, textbook, and generic identifier naming patterns."""

    @classmethod
    def analyze(cls, code: str, language: SupportedLanguage = SupportedLanguage.PYTHON) -> IdentifierAnalysisResult:
        """Perform static AST and token inspection of local variable names."""
        signals: List[ProvenanceSignal] = []
        generic_vars_found: Set[str] = set()
        repeated_patterns: List[str] = []

        if language == SupportedLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        var_name = node.id
                        var_lower = var_name.lower()
                        if var_lower in GENERIC_VARIABLE_NAMES or (
                            var_lower.startswith(("temp_", "result_", "final_")) and len(var_lower) > 6
                        ):
                            generic_vars_found.add(var_name)
                            signals.append(
                                ProvenanceSignal(
                                    signal_type="generic_identifier",
                                    severity="low",
                                    confidence=0.8,
                                    description=f"Formulaic generic identifier name '{var_name}'",
                                    file_location={"line_start": node.lineno},
                                    evidence=var_name,
                                )
                            )
            except Exception:
                pass

        # Regex fallback for multi-language identifier patterns
        if not generic_vars_found:
            for g_var in GENERIC_VARIABLE_NAMES:
                pattern = rf"\b{g_var}\b"
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for m in matches:
                    line_num = code[: m.start()].count("\n") + 1
                    signals.append(
                        ProvenanceSignal(
                            signal_type="generic_identifier",
                            severity="low",
                            confidence=0.75,
                            description=f"Formulaic generic identifier name '{m.group(0)}'",
                            file_location={"line_start": line_num},
                            evidence=m.group(0),
                        )
                    )

        if len(generic_vars_found) >= 3:
            repeated_patterns.append(f"High density of generic variable names: {', '.join(list(generic_vars_found)[:4])}")

        return IdentifierAnalysisResult(
            generic_identifiers_count=len(signals),
            generic_identifiers=signals,
            repeated_naming_patterns=repeated_patterns,
        )
