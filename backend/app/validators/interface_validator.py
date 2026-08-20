"""Public Interface Validator ensuring external contracts remain invariant."""

import ast
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.schemas import ValidationCheckResult, ValidationVerdict
from app.validators.base import BaseValidatorStage


def _extract_public_interfaces(tree: ast.AST) -> Dict[str, Any]:
    """Extract public API contracts: functions, signatures, classes, module constants, and __all__."""
    interfaces: Dict[str, Any] = {
        "functions": {},
        "classes": {},
        "module_constants": set(),
        "exported_all": None,
    }

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            interfaces["functions"][node.name] = {
                "name": node.name,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "posonlyargs": [a.arg for a in node.args.posonlyargs],
                "args": [a.arg for a in node.args.args],
                "kwonlyargs": [a.arg for a in node.args.kwonlyargs],
                "vararg": node.args.vararg.arg if node.args.vararg else None,
                "kwarg": node.args.kwarg.arg if node.args.kwarg else None,
                "defaults_count": len(node.args.defaults),
                "kw_defaults_count": len([d for d in node.args.kw_defaults if d is not None]),
            }
        elif isinstance(node, ast.ClassDef):
            methods = {}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods[item.name] = {
                        "name": item.name,
                        "is_async": isinstance(item, ast.AsyncFunctionDef),
                        "args": [a.arg for a in item.args.posonlyargs + item.args.args],
                        "kwonlyargs": [a.arg for a in item.args.kwonlyargs],
                        "vararg": item.args.vararg.arg if item.args.vararg else None,
                        "kwarg": item.args.kwarg.arg if item.args.kwarg else None,
                        "defaults_count": len(item.args.defaults),
                    }
            bases = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    bases.append(str(b))
            interfaces["classes"][node.name] = {
                "name": node.name,
                "bases": bases,
                "methods": methods,
            }
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                        exported = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exported.append(elt.value)
                        interfaces["exported_all"] = sorted(exported)
                    elif target.id.isupper():
                        interfaces["module_constants"].add(target.id)

    return interfaces


class PublicInterfaceValidator(BaseValidatorStage):
    """Guarantees that public interfaces, function signatures, parameters, and classes remain invariant."""

    @property
    def name(self) -> str:
        return "Public Interface & Signatures"

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
                details="Baseline or candidate AST unavailable for interface comparison.",
            )

        orig_iface = _extract_public_interfaces(orig_ast)
        trans_iface = _extract_public_interfaces(trans_ast)

        mismatches: List[str] = []

        # 1. Compare Functions & Signatures
        orig_fn_names = set(orig_iface["functions"].keys())
        trans_fn_names = set(trans_iface["functions"].keys())

        if orig_fn_names != trans_fn_names:
            missing = orig_fn_names - trans_fn_names
            added = trans_fn_names - orig_fn_names
            if missing:
                mismatches.append(f"Missing top-level function(s): {', '.join(missing)}")
            if added:
                mismatches.append(f"Unexpected top-level function(s) added: {', '.join(added)}")
        else:
            for fn_name, orig_sig in orig_iface["functions"].items():
                trans_sig = trans_iface["functions"][fn_name]
                if orig_sig["args"] != trans_sig["args"]:
                    mismatches.append(
                        f"Function '{fn_name}' positional arguments mutated from {orig_sig['args']} to {trans_sig['args']}"
                    )
                if orig_sig["kwonlyargs"] != trans_sig["kwonlyargs"]:
                    mismatches.append(
                        f"Function '{fn_name}' keyword-only parameters mutated"
                    )
                if orig_sig["vararg"] != trans_sig["vararg"]:
                    mismatches.append(f"Function '{fn_name}' *args parameter mutated")
                if orig_sig["kwarg"] != trans_sig["kwarg"]:
                    mismatches.append(f"Function '{fn_name}' **kwargs parameter mutated")
                if orig_sig["defaults_count"] != trans_sig["defaults_count"]:
                    mismatches.append(
                        f"Function '{fn_name}' default arguments count mutated"
                    )

        # 2. Compare Classes & Methods
        orig_cls_names = set(orig_iface["classes"].keys())
        trans_cls_names = set(trans_iface["classes"].keys())

        if orig_cls_names != trans_cls_names:
            missing = orig_cls_names - trans_cls_names
            added = trans_cls_names - orig_cls_names
            if missing:
                mismatches.append(f"Missing class(es): {', '.join(missing)}")
            if added:
                mismatches.append(f"Unexpected class(es) added: {', '.join(added)}")
        else:
            for cls_name, orig_cls in orig_iface["classes"].items():
                trans_cls = trans_iface["classes"][cls_name]
                if orig_cls["bases"] != trans_cls["bases"]:
                    mismatches.append(f"Class '{cls_name}' base inheritance hierarchy mutated")
                
                orig_methods = set(orig_cls["methods"].keys())
                trans_methods = set(trans_cls["methods"].keys())
                if orig_methods != trans_methods:
                    mismatches.append(f"Class '{cls_name}' methods changed")
                else:
                    for meth_name, orig_m in orig_cls["methods"].items():
                        trans_m = trans_cls["methods"][meth_name]
                        if orig_m["args"] != trans_m["args"]:
                            mismatches.append(
                                f"Method '{cls_name}.{meth_name}' parameters mutated from {orig_m['args']} to {trans_m['args']}"
                            )

        # 3. Compare __all__ exports if present
        if orig_iface["exported_all"] is not None:
            if orig_iface["exported_all"] != trans_iface["exported_all"]:
                mismatches.append(
                    f"Module __all__ exports mutated from {orig_iface['exported_all']} to {trans_iface['exported_all']}"
                )

        # 4. Compare Module-level Constants
        if orig_iface["module_constants"] != trans_iface["module_constants"]:
            mismatches.append("Top-level module constants were modified or renamed")

        if mismatches:
            return ValidationCheckResult(
                check_name=self.name,
                passed=False,
                severity=ValidationVerdict.FAILED,
                details=f"Public interface invariant violations: {'; '.join(mismatches)}",
                context={"violations": mismatches},
            )

        fn_count = len(orig_iface["functions"])
        cls_count = len(orig_iface["classes"])
        return ValidationCheckResult(
            check_name=self.name,
            passed=True,
            severity=ValidationVerdict.PASSED,
            details=f"All {fn_count} function signature(s) and {cls_count} class definition(s) remain strictly invariant.",
            context={"functions_validated": fn_count, "classes_validated": cls_count},
        )
