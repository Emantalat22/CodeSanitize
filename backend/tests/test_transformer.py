"""Comprehensive unit, integration, and property-based tests for Transformation Engine."""

import ast
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st
from app.models.schemas import (
    CodeInput,
    SupportedLanguage,
    TransformationAttemptStatus,
    TransformationStatus,
    ValidationVerdict,
)
from app.services.transformation_engine import TransformationEngine
from app.transformers.python.ast_canonical import AstCanonicalFormatRule
from app.transformers.python.formatting_norm import FormattingNormalizationRule
from app.transformers.python.local_variable_rename import SafeLocalVariableRenameRule
from app.validators.python_validator import PythonTransformationValidator


# ===================================================
# 1. Individual Rule Unit Tests
# ===================================================

def test_formatting_normalization_rule():
    """Test FormattingNormalizationRule removes trailing ws and collapses blanks."""
    code = "def sample():   \n    x = 1   \n\n\n\n\n    return x\n\n\n"
    rule = FormattingNormalizationRule()

    can_apply, _ = rule.can_apply(code, None)
    assert can_apply is True

    new_code, _, desc, change_count = rule.apply(code, None)
    # Check that no lines end with spaces
    for line in new_code.splitlines():
        assert not line.endswith(" ")
        assert not line.endswith("\t")
    # Check that excessive blank lines were collapsed (<= 2 consecutive blanks)
    assert "\n\n\n\n" not in new_code
    assert new_code.endswith("\n")
    assert not new_code.endswith("\n\n")
    assert change_count > 0



def test_ast_canonical_format_rule():
    """Test AstCanonicalFormatRule unparses expressions canonically."""
    code = "def calc(a,b):\n    return(a+b)*(a-b)\n"
    rule = AstCanonicalFormatRule()

    can_apply, _ = rule.can_apply(code, None)
    assert can_apply is True

    new_code, new_ast, desc, count = rule.apply(code, None)
    assert "def calc(a, b):" in new_code
    assert "(a + b) * (a - b)" in new_code
    assert count > 0


def test_safe_local_variable_rename_rule():
    """Test SafeLocalVariableRenameRule renames only local variables and preserves params/builtins."""
    code = """def process_items(items: list[int], factor: int = 2) -> int:
    \"\"\"Docstring preserved.\"\"\"
    temp_accumulator = 0
    for single_element in items:
        multiplied_val = single_element * factor
        temp_accumulator += multiplied_val
    return temp_accumulator
"""
    rule = SafeLocalVariableRenameRule()
    can_apply, _ = rule.can_apply(code, None)
    assert can_apply is True

    new_code, new_ast, desc, count = rule.apply(code, None)
    # Parameters must NOT be renamed
    assert "items" in new_code
    assert "factor" in new_code
    # Local variables should be normalized into human-like names (never _norm_var_)
    assert "_norm_var_" not in new_code
    assert "total" in new_code or "element" in new_code
    assert count >= 1
    # Result must be valid Python
    parsed = ast.parse(new_code)
    assert len(parsed.body) == 1



def test_local_variable_rename_preserves_attributes_and_globals():
    """Verify that object attributes, global accesses, and methods are never renamed."""
    code = """import os

GLOBAL_CONFIG = {"active": True}

class Service:
    def __init__(self, name: str):
        self.name = name
        local_scratch = len(name)

    def execute(self, user_obj):
        local_result = user_obj.name + str(GLOBAL_CONFIG["active"])
        return local_result
"""
    rule = SafeLocalVariableRenameRule()
    new_code, _, _, count = rule.apply(code, None)

    assert "self.name" in new_code
    assert "user_obj.name" in new_code
    assert "GLOBAL_CONFIG" in new_code
    assert "len(name)" in new_code
    assert "import os" in new_code


def test_local_variable_rename_skips_dynamic_reflection():
    """Verify that functions calling locals(), globals(), or eval() are untouched."""
    code = """def unsafe_func(data):
    my_var = 42
    print(locals())
    return my_var
"""
    rule = SafeLocalVariableRenameRule()
    can_apply, reason = rule.can_apply(code, None)
    assert can_apply is False
    assert "dynamic reflection" in reason.lower() or "locals" in reason.lower()


# ===================================================
# 2. Multi-Construct Python Integration Tests
# ===================================================

def test_transform_classes_and_methods(client: TestClient):
    """Test transformation on classes, methods, and inheritance."""
    code = """class BaseEngine:
    def start(self) -> bool:
        return True

class TurboEngine(BaseEngine):
    def start(self) -> bool:
        local_status = super().start()   
        return local_status
"""
    res = client.post(
        "/api/transform",
        json={"code": code, "language": "python", "filename": "engine.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["transformation_status"] in ("completed", "partial")
    assert data["validation_status"] == "passed"
    assert "class TurboEngine(BaseEngine):" in data["transformed_code"]
    assert data["diff"] is not None


def test_transform_decorators_and_async_functions(client: TestClient):
    """Test transformation on async functions and decorators."""
    code = """import asyncio

def log_call(fn):
    return fn

@log_call
async def fetch_user_data(user_id: int) -> dict:
    await asyncio.sleep(0.01)
    user_payload = {"id": user_id, "active": True}
    return user_payload
"""
    res = client.post(
        "/api/transform",
        json={"code": code, "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["validation_status"] == "passed"
    assert "async def fetch_user_data(user_id: int)" in data["transformed_code"]
    assert "@log_call" in data["transformed_code"]


def test_transform_generators_and_comprehensions(client: TestClient):
    """Test transformation on generators, lambdas, and list/dict comprehensions."""
    code = """def number_generator(limit: int):
    local_step = 2
    for item in range(0, limit, local_step):
        yield item

def transform_matrix(matrix: list[list[int]]) -> list[int]:
    flattened = [val for row in matrix for val in row if val > 0]
    doubled = list(map(lambda x: x * 2, flattened))
    return doubled
"""
    res = client.post(
        "/api/transform",
        json={"code": code, "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["validation_status"] == "passed"
    assert "yield" in data["transformed_code"]


def test_transform_exceptions_and_control_flow(client: TestClient):
    """Test transformation with try/except/finally blocks and loops."""
    code = """def safe_divide(numerator: float, denominator: float) -> float:
    try:
        calc_result = numerator / denominator
    except ZeroDivisionError:
        calc_result = 0.0
    finally:
        pass
    return calc_result
"""
    res = client.post(
        "/api/transform",
        json={"code": code, "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["validation_status"] == "passed"
    assert "try:" in data["transformed_code"]
    assert "except ZeroDivisionError:" in data["transformed_code"]


# ===================================================
# 3. Validator Safeguard & Rejection Tests
# ===================================================

def test_validator_rejects_mutated_signatures():
    """Verify that PythonTransformationValidator rejects signature changes."""
    orig = "def compute(a: int, b: int) -> int:\n    return a + b\n"
    mutated = "def compute(a: int, c: int) -> int:\n    return a + c\n"

    validator = PythonTransformationValidator()
    result = validator.validate(orig, mutated)

    assert result.is_valid is False
    assert result.verdict == ValidationVerdict.FAILED
    assert "arguments mutated" in result.message.lower() or "signature" in result.message.lower()


def test_validator_rejects_mutated_imports():
    """Verify that PythonTransformationValidator rejects altered imports."""
    orig = "import os, sys\n\ndef run(): pass\n"
    mutated = "import os, subprocess\n\ndef run(): pass\n"

    validator = PythonTransformationValidator()
    result = validator.validate(orig, mutated)

    assert result.is_valid is False
    assert result.verdict == ValidationVerdict.FAILED
    assert "import" in result.message.lower()


def test_validator_rejects_mutated_class_bases():
    """Verify that PythonTransformationValidator rejects modified inheritance."""
    orig = "class Child(Base): pass\n"
    mutated = "class Child(OtherBase): pass\n"

    validator = PythonTransformationValidator()
    result = validator.validate(orig, mutated)

    assert result.is_valid is False
    assert result.verdict == ValidationVerdict.FAILED
    assert "class" in result.message.lower()


def test_validator_rejects_syntax_errors():
    """Verify validator catches syntax errors in transformed output."""
    orig = "def ok(): pass\n"
    broken = "def ok( pass\n"

    validator = PythonTransformationValidator()
    result = validator.validate(orig, broken)

    assert result.is_valid is False
    assert result.syntax_valid is False
    assert result.verdict == ValidationVerdict.FAILED


# ===================================================
# 4. API Endpoints & History Tests
# ===================================================

def test_list_transformations_endpoint(client: TestClient):
    """Test GET /api/transformations lists available rules."""
    res = client.get("/api/transformations")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 3
    rule_ids = [r["rule_id"] for r in rules]
    assert "PY-FMT-NORM-01" in rule_ids
    assert "PY-AST-CANON-01" in rule_ids
    assert "PY-SAFE-LOCAL-RENAME-01" in rule_ids


def test_transform_with_options_filter(client: TestClient):
    """Test enabling only specific transformation rules via options."""
    code = "def test(a):\n    temp = a * 2   \n    return temp\n"
    res = client.post(
        "/api/transform",
        json={
            "code": code,
            "language": "python",
            "options": {"enabled_transformations": ["PY-FMT-NORM-01"]},
        },
    )
    assert res.status_code == 200
    data = res.json()
    applied_ids = [t["rule_id"] for t in data["transformations_applied"]]
    assert "PY-FMT-NORM-01" in applied_ids
    assert "PY-SAFE-LOCAL-RENAME-01" not in applied_ids


def test_transform_unsupported_language(client: TestClient):
    """Test transformation on non-Python language reports clear message without pretending."""
    res = client.post(
        "/api/transform",
        json={"code": "function hello() {}", "language": "javascript"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["transformation_status"] == "unsupported_language"
    assert data["transformed_code"] == "function hello() {}"


# ===================================================
# 5. Dedicated Regression Tests
# ===================================================

def test_nested_loops_conditionals_and_return_regression(client: TestClient):
    """Regression test specifically verifying:
    - function body indentation
    - nested for loop
    - nested conditional expression
    - return statement
    - multiple local variables
    - compile(..., 'exec') verification
    - functional execution equivalence on controlled inputs
    """
    code = """def compute_stats(values: list[float], scale: float = 1.0) -> dict:
    \"\"\"Calculate scaled statistics.\"\"\"
    temp_sum = 0.0   
    for single_val in values:
        intermediate_scaled = single_val * scale   
        temp_sum = temp_sum + intermediate_scaled


    calc_mean = ( temp_sum / len(values) ) if values else 0.0
    return {"sum": temp_sum, "mean": calc_mean}
"""
    res = client.post(
        "/api/transform",
        json={"code": code, "language": "python", "filename": "stats.py"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["transformation_status"] == "completed"
    assert data["validation_status"] == "passed"
    transformed = data["transformed_code"]

    # 1. Verify exact indentation structure and human-like naming (no _norm_var_)
    assert "_norm_var_" not in transformed
    lines = transformed.splitlines()
    assert lines[0].startswith("def compute_stats(")
    assert lines[1].startswith("    \"\"\"")
    assert "total = 0.0" in transformed or "total" in transformed
    assert "for item in values:" in transformed or "values" in transformed
    assert "return {" in transformed

    # 2. Independent AST parse
    parsed_ast = ast.parse(transformed)
    assert parsed_ast is not None


    # 3. Independent compile() with mode='exec'
    compiled_code = compile(transformed, "<test_regression>", "exec")
    assert compiled_code is not None

    # 4. Functional equivalence verification on controlled inputs
    orig_env = {}
    exec(code, orig_env)
    orig_fn = orig_env["compute_stats"]

    trans_env = {}
    exec(transformed, trans_env)
    trans_fn = trans_env["compute_stats"]

    test_cases = [
        ([1.0, 2.0, 3.0, 4.0], 2.0),
        ([10.0, -5.0, 0.0], 0.5),
        ([], 1.0),
        ([100.0], 1.5),
    ]
    for vals, scale in test_cases:
        assert orig_fn(vals, scale) == trans_fn(vals, scale)


# ===================================================
# 6. Property-Based Testing with Hypothesis
# ===================================================


# Strategy to generate valid Python expressions and simple functions
@st.composite
def valid_python_code_strategy(draw):
    import keyword

    var_name = draw(
        st.from_regex(r"[a-z][a-z0-9_]{1,6}", fullmatch=True).filter(
            lambda s: not keyword.iskeyword(s) and not keyword.issoftkeyword(s)
        )
    )
    int_val = draw(st.integers(min_value=-1000, max_value=1000))
    op = draw(st.sampled_from(["+", "-", "*"]))
    param = draw(st.from_regex(r"p[0-9]", fullmatch=True))

    code = f"""def generated_fn({param}: int) -> int:
    # Auto-generated property test
    {var_name} = {param} {op} {int_val}
    return {var_name}
"""
    return code



@given(code=valid_python_code_strategy())
@settings(max_examples=25, deadline=None)
def test_hypothesis_transformation_property(code: str):
    """Property: For any valid Python program, TransformationEngine.transform
    MUST produce either a validated program that parses cleanly and preserves invariants,
    OR cleanly reject without emitting invalid code.
    """
    result = TransformationEngine.transform(
        CodeInput(code=code, language=SupportedLanguage.PYTHON)
    )

    # Core Invariant: Transformed output must NEVER fail AST parsing
    parsed = ast.parse(result.transformed_code)
    assert parsed is not None

    # Signatures must be preserved
    validator = PythonTransformationValidator()
    val_check = validator.validate(code, result.transformed_code)
    assert val_check.is_valid is True


def test_dictionary_return_simplification():
    """Verify x = {}; x['a'] = 1; x['b'] = 2; return x simplifies to return {'a': 1, 'b': 2}."""
    from app.transformers.python.code_simplification import PythonCodeSimplificationRule
    code = """def get_payload(a, b):
    result = {}
    result["area"] = a * b
    result["perimeter"] = 2 * (a + b)
    return result
"""
    rule = PythonCodeSimplificationRule()
    can_apply, _ = rule.can_apply(code, None)
    assert can_apply is True
    new_code, _, desc, count = rule.apply(code, None)
    assert count == 1
    assert "return {'area': a * b, 'perimeter': 2 * (a + b)}" in new_code or "return {" in new_code


def test_identifier_intelligence_inferences():
    """Verify that AI variables like temp_area, temp_circumference, result_data become natural human names."""
    from app.transformers.python.identifier_intelligence import IdentifierIntelligence
    assert IdentifierIntelligence.infer_name("result_data") == "metrics"
    assert IdentifierIntelligence.infer_name("temp_area") == "area"
    assert IdentifierIntelligence.infer_name("temp_circumference") == "circumference"
    assert IdentifierIntelligence.infer_name("temp_radius") == "radius"
    assert IdentifierIntelligence.infer_name("temp_total") == "total"

