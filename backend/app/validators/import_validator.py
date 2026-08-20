"""Import and dependency invariance validator for Python."""

import ast
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import ValidationCheckResult, ValidationVerdict
from app.validators.base import BaseValidatorStage


def _extract_normalized_imports(tree: ast.AST) -> List[Tuple[str, Optional[str], Optional[int], List[Tuple[str, Optional[str]]]]]:
    """Extract structured, normalized representation of all imports in order of appearance."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases = sorted([(alias.name, alias.asname) for alias in node.names])
            imports.append(("import", None, None, aliases))
        elif isinstance(node, ast.ImportFrom):
            aliases = sorted([(alias.name, alias.asname) for alias in node.names])
            imports.append(("from_import", node.module, node.level, aliases))
    return sorted(imports, key=lambda x: (x[0], x[1] or "", x[2] or 0, str(x[3])))


class ImportValidator(BaseValidatorStage):
    """Enforces 100% strict invariance of module imports, aliases, relative imports, and dependencies."""

    @property
    def name(self) -> str:
        return "Imports & Dependencies"

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
                details="Baseline or candidate AST unavailable for import comparison.",
            )

        orig_imports = _extract_normalized_imports(orig_ast)
        trans_imports = _extract_normalized_imports(trans_ast)

        if orig_imports != trans_imports:
            missing = [imp for imp in orig_imports if imp not in trans_imports]
            added = [imp for imp in trans_imports if imp not in orig_imports]

            reasons = []
            if missing:
                reasons.append(f"Imports removed/modified: {missing}")
            if added:
                reasons.append(f"Unexpected imports added: {added}")

            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Import invariance violation: {'; '.join(reasons)}",
                context={"violations": reasons, "original_imports": orig_imports, "transformed_imports": trans_imports},
            )

        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details=f"All {len(orig_imports)} import statement(s) and aliases are strictly preserved.",
            context={"import_count": len(orig_imports)},
        )
