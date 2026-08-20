"""Conservative static side-effect sensitivity analyzer for Python."""

import ast
from typing import Any, Dict, List, Optional, Set
from app.models.schemas import ValidationCheckResult, ValidationRiskFlag, ValidationVerdict
from app.validators.base import BaseValidatorStage

FILE_IO_CALLS = {"open", "read", "write", "close", "unlink", "remove", "mkdir", "rmdir"}
FILE_IO_MODULES = {"io", "pathlib", "shutil", "tempfile"}

SUBPROCESS_MODULES = {"subprocess"}
SUBPROCESS_CALLS = {"system", "popen", "spawn"}

NETWORK_MODULES = {"urllib", "requests", "http", "socket", "httpx", "aiohttp", "urllib3"}

ENV_CALLS = {"getenv", "putenv"}

RANDOM_TIME_MODULES = {"random", "secrets", "time", "datetime"}

THREADING_MODULES = {"threading", "multiprocessing", "concurrent.futures", "asyncio"}


class SideEffectScanner(ast.NodeVisitor):
    """Scans AST for potentially side-effect-sensitive external operations without executing them."""

    def __init__(self):
        self.file_io_detected = False
        self.subprocess_detected = False
        self.network_detected = False
        self.env_detected = False
        self.random_time_detected = False
        self.threading_detected = False
        self.risk_flags: Set[ValidationRiskFlag] = set()
        self.detected_items: List[str] = []

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ("open",):
                self.file_io_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_FILE_IO)
                self.detected_items.append("Builtin file open()")
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if isinstance(node.func.value, ast.Name):
                val_id = node.func.value.id
                if val_id == "os" and attr in SUBPROCESS_CALLS:
                    self.subprocess_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_SUBPROCESS)
                    self.detected_items.append(f"os.{attr}() execution")
                elif val_id == "os" and attr in ENV_CALLS:
                    self.env_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_ENV)
                    self.detected_items.append(f"os.{attr}() access")
                elif val_id in SUBPROCESS_MODULES:
                    self.subprocess_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_SUBPROCESS)
                    self.detected_items.append(f"subprocess.{attr}() execution")
                elif val_id in NETWORK_MODULES:
                    self.network_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_NETWORK)
                    self.detected_items.append(f"{val_id}.{attr}() network call")
                elif val_id in RANDOM_TIME_MODULES:
                    self.random_time_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_RANDOM_TIME)
                    self.detected_items.append(f"{val_id}.{attr}() time/random")
                elif val_id in THREADING_MODULES:
                    self.threading_detected = True
                    self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_THREADING)
                    self.detected_items.append(f"{val_id}.{attr}() concurrent operation")

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in SUBPROCESS_MODULES:
                self.subprocess_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_SUBPROCESS)
                self.detected_items.append(f"Import {alias.name}")
            elif base_mod in NETWORK_MODULES:
                self.network_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_NETWORK)
                self.detected_items.append(f"Import {alias.name}")
            elif base_mod in THREADING_MODULES:
                self.threading_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_THREADING)
                self.detected_items.append(f"Import {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in SUBPROCESS_MODULES:
                self.subprocess_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_SUBPROCESS)
                self.detected_items.append(f"Import from {node.module}")
            elif base_mod in NETWORK_MODULES:
                self.network_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_NETWORK)
                self.detected_items.append(f"Import from {node.module}")
            elif base_mod in THREADING_MODULES:
                self.threading_detected = True
                self.risk_flags.add(ValidationRiskFlag.SIDE_EFFECT_THREADING)
                self.detected_items.append(f"Import from {node.module}")
        self.generic_visit(node)


class SideEffectValidator(BaseValidatorStage):
    """Conservatively flags potentially side-effect-sensitive code without executing it."""

    @property
    def name(self) -> str:
        return "Side-Effect Sensitivity Analysis"

    def validate(
        self,
        orig_code: str,
        trans_code: str,
        orig_ast: Optional[ast.AST],
        trans_ast: Optional[ast.AST],
        rule_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ValidationCheckResult:
        orig_tree = orig_ast or (ast.parse(orig_code) if orig_code.strip() else None)
        trans_tree = trans_ast or (ast.parse(trans_code) if trans_code.strip() else None)

        if trans_tree is None:
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.PASSED,
                details="Empty code - no side-effects detected.",
            )

        orig_scanner = SideEffectScanner()
        if orig_tree:
            orig_scanner.visit(orig_tree)

        trans_scanner = SideEffectScanner()
        trans_scanner.visit(trans_tree)

        # Check if candidate code introduced NEW unexpected side effects
        new_side_effects = set(trans_scanner.detected_items) - set(orig_scanner.detected_items)
        if new_side_effects:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.WARNING,
                details=f"Transformation introduced new side-effect-sensitive operations: {', '.join(new_side_effects)}",
                context={
                    "risk_flags": [f.value for f in trans_scanner.risk_flags],
                    "new_items": list(new_side_effects),
                },
            )

        if trans_scanner.detected_items:
            # Side effects exist in the source, but were preserved invariantly
            return ValidationCheckResult(
                check_name=self.name,
                passed=True,
                severity=ValidationVerdict.PASSED,
                details=f"Side-effect sensitivity identified: {', '.join(set(trans_scanner.detected_items))} (invariants preserved).",
                context={
                    "risk_flags": [f.value for f in trans_scanner.risk_flags],
                    "items": list(set(trans_scanner.detected_items)),
                },
            )

        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details="No external side-effect-sensitive operations (file I/O, subprocess, network, concurrency) detected.",
        )
