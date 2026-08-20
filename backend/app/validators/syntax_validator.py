"""Syntax validation stage for transformed candidate code."""

import ast
from typing import Any, Dict, Optional
from app.models.schemas import ValidationCheckResult, ValidationVerdict
from app.validators.base import BaseValidatorStage


class SyntaxValidator(BaseValidatorStage):
    """Verifies that transformed candidate code parses into a syntactically valid AST."""

    @property
    def name(self) -> str:
        return "Syntax Integrity"

    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST],
        trans_ast: Optional[ast.AST],
        rule_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationCheckResult:
        if trans_ast is not None:
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.PASSED,
                details="Transformed candidate parsed cleanly into a valid AST without syntax errors.",
            )

        try:
            ast.parse(trans_code, filename="<transformed>")
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.PASSED,
                details="Transformed candidate parsed cleanly into a valid AST without syntax errors.",
            )
        except SyntaxError as e:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Transformed code contains syntax error on line {e.lineno}: {e.msg}",
                context={"line": e.lineno, "offset": e.offset, "text": e.text},
            )
        except Exception as e:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Parser exception during syntax validation: {str(e)}",
            )
