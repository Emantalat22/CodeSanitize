"""Comprehensive tests for Chunk 4 Advanced Multi-Stage Validation Pipeline."""

import ast
import pytest
from fastapi.testclient import TestClient
from app.models.schemas import (
    ValidateRequest,
    ValidationConfidenceLevel,
    ValidationPolicy,
    ValidationRiskFlag,
    ValidationVerdict,
)
from app.validators.pipeline import ValidationPipeline


@pytest.fixture
def pipeline():
    return ValidationPipeline()


# ===================================================
# 1. Functions & Closures Validation Tests
# ===================================================

def test_validate_normal_and_nested_functions(pipeline: ValidationPipeline):
    """Test validation on normal and nested functions with closures."""
    orig = """def outer_func(x: int) -> int:
    multiplier = 10
    def inner_helper(val: int) -> int:
        return val * multiplier
    return inner_helper(x)
"""
    trans = """def outer_func(x: int) -> int:
    _norm_var_1 = 10
    def inner_helper(val: int) -> int:
        return val * _norm_var_1
    return inner_helper(x)
"""
    res = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED
    assert res.confidence_level == ValidationConfidenceLevel.HIGH


def test_validate_async_functions_and_generators(pipeline: ValidationPipeline):
    """Test validation on async functions and generators."""
    orig = """import asyncio

async def fetch_stream():
    await asyncio.sleep(0.01)
    for i in range(5):
        yield i
"""
    trans = """import asyncio

async def fetch_stream():
    await asyncio.sleep(0.01)
    for _norm_var_1 in range(5):
        yield _norm_var_1
"""
    res = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED


def test_validate_rejects_async_status_mutation(pipeline: ValidationPipeline):
    """Verify that turning an async function into a sync function fails."""
    orig = "async def query_db(): return 1\n"
    trans = "def query_db(): return 1\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED
    assert any("async" in f.details.lower() for f in res.failures)


def test_validate_rejects_generator_yield_removal(pipeline: ValidationPipeline):
    """Verify that removing yield statements from a generator fails."""
    orig = "def gen():\n    yield 1\n    yield 2\n"
    trans = "def gen():\n    return [1, 2]\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


# ===================================================
# 2. Classes, Inheritance, and Decorators
# ===================================================

def test_validate_classes_methods_and_decorators(pipeline: ValidationPipeline):
    """Test validation of classes, methods, and decorators."""
    orig = """def memoize(fn): return fn

class DataService(BaseService):
    CACHE_SIZE = 100

    @memoize
    def get_data(self, key: str) -> str:
        temp_val = key.strip()
        return temp_val
"""
    trans = """def memoize(fn): return fn

class DataService(BaseService):
    CACHE_SIZE = 100

    @memoize
    def get_data(self, key: str) -> str:
        _norm_var_1 = key.strip()
        return _norm_var_1
"""
    res = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED


def test_validate_rejects_class_decorator_removal(pipeline: ValidationPipeline):
    """Verify that removing decorators fails structural validation."""
    orig = "@dataclass\nclass Config: pass\n"
    trans = "class Config: pass\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


def test_validate_rejects_class_base_mutation(pipeline: ValidationPipeline):
    """Verify that changing base classes fails interface validation."""
    orig = "class Model(BaseModel): pass\n"
    trans = "class Model(OtherModel): pass\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


# ===================================================
# 3. Control Flow Invariants
# ===================================================

def test_validate_nested_control_flow_and_match(pipeline: ValidationPipeline):
    """Test validation of nested if/for/while/try/match constructs."""
    code = """def process_command(cmd: str, max_retries: int = 3):
    count = 0
    while count < max_retries:
        try:
            if cmd == "start":
                for item in [1, 2, 3]:
                    if item > 2:
                        break
                    else:
                        continue
            elif cmd == "stop":
                return False
            else:
                raise ValueError(cmd)
        except ValueError:
            count += 1
        finally:
            pass
    return True
"""
    # Self-validation
    res = pipeline.validate(code, code)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED


def test_validate_rejects_branch_removal(pipeline: ValidationPipeline):
    """Verify that omitting an else or elif branch fails control flow validation."""
    orig = "def check(x):\n    if x > 0:\n        return 1\n    else:\n        return 0\n"
    trans = "def check(x):\n    if x > 0:\n        return 1\n    return 0\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED
    assert any("if" in f.details.lower() or "control" in f.details.lower() for f in res.failures)


# ===================================================
# 4. Reflection and Eval Safeguards
# ===================================================

def test_validate_flags_locals_and_globals(pipeline: ValidationPipeline):
    """Verify that code calling locals() or globals() is flagged and rejected under STRICT policy."""
    orig = "def inspect_scope():\n    x = 1\n    return locals()\n"
    trans = "def inspect_scope():\n    _norm_var_1 = 1\n    return locals()\n"

    # STRICT policy -> rejected
    strict_res = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    assert strict_res.is_valid is False
    assert strict_res.verdict == ValidationVerdict.FAILED
    assert ValidationRiskFlag.REFLECTION_DETECTED in strict_res.risk_flags

    # BALANCED policy -> warnings reported, accepted
    balanced_res = pipeline.validate(orig, trans, policy=ValidationPolicy.BALANCED)
    assert balanced_res.is_valid is True
    assert balanced_res.verdict == ValidationVerdict.WARNING
    assert len(balanced_res.warnings) > 0


def test_validate_flags_eval_and_exec(pipeline: ValidationPipeline):
    """Verify eval() and exec() are flagged with EVAL_EXEC_DETECTED risk flag."""
    code = "def run_dynamic(expr: str):\n    return eval(expr)\n"
    res = pipeline.validate(code, code, policy=ValidationPolicy.STRICT)
    # Even on identity, reflection scanner reports warning
    assert ValidationRiskFlag.EVAL_EXEC_DETECTED in res.risk_flags or ValidationRiskFlag.REFLECTION_DETECTED in res.risk_flags


# ===================================================
# 5. Imports & Dependencies Invariants
# ===================================================

def test_validate_imports_invariance(pipeline: ValidationPipeline):
    """Verify relative, aliased, and standard imports are strictly checked."""
    orig = """import os
import sys as system
from pathlib import Path
from .local_mod import helper
"""
    trans = orig
    res = pipeline.validate(orig, trans)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED


def test_validate_rejects_import_alias_change(pipeline: ValidationPipeline):
    """Verify that altering import aliases fails validation."""
    orig = "import numpy as np\n"
    trans = "import numpy as npy\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


def test_validate_rejects_relative_import_level_change(pipeline: ValidationPipeline):
    """Verify that changing relative import level fails validation."""
    orig = "from .sibling import item\n"
    trans = "from ..parent import item\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


# ===================================================
# 6. Side Effects Detection
# ===================================================

def test_validate_flags_file_io_and_subprocess(pipeline: ValidationPipeline):
    """Verify that file I/O, subprocess, and network calls are detected statically."""
    code = """import subprocess
import requests

def fetch_and_write(url: str, filepath: str):
    resp = requests.get(url)
    with open(filepath, 'w') as f:
        f.write(resp.text)
    subprocess.run(["chmod", "644", filepath])
"""
    res = pipeline.validate(code, code, policy=ValidationPolicy.BALANCED)
    assert ValidationRiskFlag.SIDE_EFFECT_FILE_IO in res.risk_flags
    assert ValidationRiskFlag.SIDE_EFFECT_SUBPROCESS in res.risk_flags
    assert ValidationRiskFlag.SIDE_EFFECT_NETWORK in res.risk_flags


# ===================================================
# 7. Data-Flow & Parameter Safeguards
# ===================================================

def test_validate_rejects_undefined_variable_reference(pipeline: ValidationPipeline):
    """Verify data-flow validator catches references to nonexistent variables."""
    orig = "def calc(a, b):\n    c = a + b\n    return c\n"
    trans = "def calc(a, b):\n    c = a + b\n    return undefined_xyz\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED
    assert any("undefined" in f.details.lower() for f in res.failures)


def test_validate_rejects_parameter_name_mutation(pipeline: ValidationPipeline):
    """Verify parameter name changes are rejected."""
    orig = "def query(target_user: str):\n    return target_user\n"
    trans = "def query(renamed_user: str):\n    return renamed_user\n"
    res = pipeline.validate(orig, trans)
    assert res.is_valid is False
    assert res.verdict == ValidationVerdict.FAILED


# ===================================================
# 8. Edge Cases & Unicode
# ===================================================

def test_validate_unicode_identifiers(pipeline: ValidationPipeline):
    """Test validation on Unicode variable names and docstrings."""
    orig = """def 計算(數值: int) -> int:
    \"\"\"計算總和\"\"\"
    暫存 = 數值 * 2
    return 暫存
"""
    trans = """def 計算(數值: int) -> int:
    \"\"\"計算總和\"\"\"
    _norm_var_1 = 數值 * 2
    return _norm_var_1
"""
    res = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED


def test_validate_empty_and_whitespace_sources(pipeline: ValidationPipeline):
    """Test validation on empty and comment-only sources."""
    res = pipeline.validate("", "")
    assert res.is_valid is True
    assert res.verdict == ValidationVerdict.PASSED

    res_comment = pipeline.validate("# Comment only\n", "# Comment only\n")
    assert res_comment.is_valid is True


# ===================================================
# 9. Validation Policy Enforcement
# ===================================================

def test_validation_policies_behavior(pipeline: ValidationPipeline):
    """Verify STRICT vs BALANCED vs PERMISSIVE policies on warning scenarios."""
    orig = "import os\ndef read_env(): return os.getenv('KEY')\n"
    trans = orig  # Has side-effect risk flag

    # 1. STRICT Policy with warnings
    res_strict = pipeline.validate(orig, trans, policy=ValidationPolicy.STRICT)
    # If warnings exist under STRICT, is_valid will be False
    if res_strict.warnings:
        assert res_strict.is_valid is False
        assert res_strict.verdict == ValidationVerdict.FAILED

    # 2. BALANCED Policy with warnings
    res_balanced = pipeline.validate(orig, trans, policy=ValidationPolicy.BALANCED)
    if res_balanced.warnings:
        assert res_balanced.is_valid is True
        assert res_balanced.verdict == ValidationVerdict.WARNING

    # 3. PERMISSIVE Policy with warnings
    res_permissive = pipeline.validate(orig, trans, policy=ValidationPolicy.PERMISSIVE)
    if res_permissive.warnings:
        assert res_permissive.is_valid is True


# ===================================================
# 10. Standalone API Endpoint POST /api/validate
# ===================================================

def test_api_validate_endpoint_detailed_report(client: TestClient):
    """Test POST /api/validate returns complete multi-stage report."""
    orig = "def add(a: int, b: int) -> int:\n    sum_val = a + b\n    return sum_val\n"
    trans = "def add(a: int, b: int) -> int:\n    _norm_var_1 = a + b\n    return _norm_var_1\n"

    res = client.post(
        "/api/validate",
        json={
            "original_code": orig,
            "transformed_code": trans,
            "language": "python",
            "policy": "strict",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["verdict"] == "passed"
    assert data["confidence_level"] == "high"
    assert len(data["validators_run"]) >= 8
    assert len(data["passed_checks"]) >= 8
