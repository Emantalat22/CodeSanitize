"""AI Pattern Normalization Composite Transformation Rule with Identifier Intelligence and Code Simplification."""

import ast
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import SupportedLanguage, TransformationSafetyLevel
from app.transformers.base import BaseTransformationRule
from app.transformers.python.code_simplification import PythonCodeSimplificationRule
from app.transformers.python.comment_norm import ProvCommentNormRule
from app.transformers.python.formatting_norm import FormattingNormalizationRule
from app.transformers.python.local_variable_rename import SafeLocalVariableRenameRule
from app.transformers.python.style_norm import ProvStyleNormRule


class AIPatternNormalizationRule(BaseTransformationRule):
    """Safely normalizes AI/synthetic style patterns into clean, experienced-developer human code."""

    def __init__(self):
        super().__init__()
        self._comment_rule = ProvCommentNormRule()
        self._simplify_rule = PythonCodeSimplificationRule()
        self._local_rename_rule = SafeLocalVariableRenameRule()
        self._style_rule = ProvStyleNormRule()
        self._fmt_rule = FormattingNormalizationRule()

    @property
    def rule_id(self) -> str:
        return "AI-PATTERN-NORM-01"

    @property
    def name(self) -> str:
        return "AI Pattern Normalization"

    @property
    def description(self) -> str:
        return "Safely normalizes AI/synthetic patterns: cleans obvious template comments, transforms generic identifiers into meaningful human names, simplifies boilerplate structures, and applies natural formatting."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [
            SupportedLanguage.PYTHON,
            SupportedLanguage.JAVASCRIPT,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVA,
            SupportedLanguage.CPP,
            SupportedLanguage.C,
            SupportedLanguage.GO,
            SupportedLanguage.RUST,
        ]

    @property
    def safety_level(self) -> TransformationSafetyLevel:
        return TransformationSafetyLevel.SAFE_CONSERVATIVE

    @property
    def default_enabled(self) -> bool:
        return True

    def can_apply(self, code: str, ast_tree: Optional[Any]) -> Tuple[bool, str]:
        if not code or not code.strip():
            return False, "Code is empty."

        can_c, _ = self._comment_rule.can_apply(code, ast_tree)
        can_simp, _ = self._simplify_rule.can_apply(code, ast_tree)
        can_r, _ = self._local_rename_rule.can_apply(code, ast_tree)
        can_s, _ = self._style_rule.can_apply(code, ast_tree)

        if can_c or can_simp or can_r or can_s:
            return True, "AI-style patterns (comments, generic names, boilerplate structures, or formatting regularities) found for normalization."

        return True, "Ready for AI pattern normalization."

    def apply(
        self, code: str, ast_tree: Optional[Any]
    ) -> Tuple[str, Optional[Any], str, int]:
        if not code or not code.strip():
            return code, ast_tree, "Empty source - no changes applied", 0

        current_code = code
        total_changes = 0
        categories_changed: Dict[str, int] = {}

        # 1. Step 1: Strip obvious redundant/template comments
        can_c, _ = self._comment_rule.can_apply(current_code, ast_tree)
        if can_c:
            new_c, _, msg_c, count_c = self._comment_rule.apply(current_code, ast_tree)
            if count_c > 0:
                current_code = new_c
                total_changes += count_c
                categories_changed["comments"] = count_c

        # 2. Step 2: Code structure and dictionary return simplification
        can_simp, _ = self._simplify_rule.can_apply(current_code, None)
        if can_simp:
            new_simp, new_tree_s, msg_simp, count_simp = self._simplify_rule.apply(current_code, None)
            if count_simp > 0:
                current_code = new_simp
                total_changes += count_simp
                categories_changed["structures"] = count_simp

        # 3. Step 3: Human identifier normalization with Identifier Intelligence
        try:
            tree = ast.parse(current_code)
            can_r, _ = self._local_rename_rule.can_apply(current_code, tree)
            if can_r:
                new_r, new_tree, msg_r, count_r = self._local_rename_rule.apply(current_code, tree)
                if count_r > 0:
                    current_code = new_r
                    total_changes += count_r
                    categories_changed["identifiers"] = count_r
        except Exception:
            pass

        # 4. Step 4: Style and spacing normalization
        can_s, _ = self._style_rule.can_apply(current_code, None)
        if can_s:
            new_s, _, msg_s, count_s = self._style_rule.apply(current_code, None)
            if count_s > 0:
                current_code = new_s
                total_changes += count_s
                categories_changed["formatting"] = count_s

        # 5. Step 5: Formatting normalization
        new_f, _, _, count_f = self._fmt_rule.apply(current_code, None)
        if new_f != current_code:
            current_code = new_f
            total_changes += max(count_f, 1)
            categories_changed["formatting"] = categories_changed.get("formatting", 0) + 1

        details = f"Normalized AI patterns: {total_changes} total modifications across {len(categories_changed)} categories into clean human code."
        return current_code, None, details, total_changes
