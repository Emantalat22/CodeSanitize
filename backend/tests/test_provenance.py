"""Tests for AI Code Provenance Analysis & Safe Normalization."""

import pytest
from fastapi.testclient import TestClient
from app.models.schemas import CodeInput, SupportedLanguage, ValidationPolicy
from app.provenance.comment_analyzer import CommentPatternAnalyzer
from app.provenance.identifier_analyzer import IdentifierPatternAnalyzer
from app.provenance.provenance_service import ProvenanceService
from app.provenance.style_analyzer import StylePatternAnalyzer
from app.services.transformation_engine import TransformationEngine
from app.transformers.python.comment_norm import ProvCommentNormRule
from app.transformers.python.style_norm import ProvStyleNormRule
from app.validators.pipeline import ValidationPipeline


def test_comment_analyzer_detects_redundant_comments():
    """Verify comment analyzer catches obvious/redundant code description comments."""
    sample_code = '''# Import necessary libraries
import math

# Define the function to calculate distance
def calculate_distance(p1, p2):
    # Initialize result variable
    result_dist = 0.0
    # Step 1: calculate squared difference
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    # Return the result
    return math.sqrt(dx * dx + dy * dy)
'''
    res = CommentPatternAnalyzer.analyze(sample_code, language=SupportedLanguage.PYTHON)
    assert res.total_comments >= 4
    assert res.redundant_comments_count >= 3
    signal_types = [s.signal_type for s in res.obvious_comments]
    assert "redundant_comment" in signal_types


def test_identifier_analyzer_detects_generic_names():
    """Verify identifier analyzer flags formulaic generic local variable names."""
    code = '''def process_batch(items):
    temp_value = 10
    result_data = []
    processed_output = {}
    for x in items:
        final_result = x * temp_value
        result_data.append(final_result)
    return result_data
'''
    res = IdentifierPatternAnalyzer.analyze(code, language=SupportedLanguage.PYTHON)
    assert res.generic_identifiers_count >= 3
    found_names = [s.evidence for s in res.generic_identifiers]
    assert "temp_value" in found_names
    assert "result_data" in found_names
    assert "final_result" in found_names


def test_style_analyzer_detects_textbook_patterns():
    """Verify style analyzer detects textbook demo entrypoints and generic exception handlers."""
    code = '''def divide(a, b):
    try:
        return a / b
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

if __name__ == '__main__':
    print("Testing output:", divide(10, 2))
'''
    res = StylePatternAnalyzer.analyze(code, language=SupportedLanguage.PYTHON)
    signal_types = [s.signal_type for s in res.signals]
    assert "generic_exception_logging" in signal_types
    assert "textbook_demo_harness" in signal_types


def test_provenance_service_aggregate_score():
    """Verify ProvenanceService aggregates findings and computes deterministic score."""
    synthetic_code = '''# Import required modules
import os

# Function to compute total
def compute_total(items):
    # Initialize empty list
    result_data = []
    temp_value = 0
    # Loop through each item in the list
    for item in items:
        # Step 1: add to temp
        temp_value += item
        result_data.append(temp_value)
    # Return the result
    return result_data

if __name__ == '__main__':
    print("Computed:", compute_total([1, 2, 3]))
'''
    report = ProvenanceService.analyze_provenance(
        CodeInput(code=synthetic_code, language=SupportedLanguage.PYTHON, filename="test.py")
    )
    assert report.provenance_score >= 50
    assert report.confidence_level in ("medium", "high")
    assert len(report.signals_detected) >= 3
    assert len(report.recommendations) >= 1


def test_api_provenance_analyze_endpoint(client: TestClient):
    """Verify HTTP POST /api/provenance/analyze endpoint."""
    payload = {
        "code": "# Initialize variable\ntemp_value = 42\n# Return the result\nreturn temp_value\n",
        "language": "python",
        "filename": "prov_test.py",
    }
    res = client.post("/api/provenance/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "provenance_score" in data
    assert "signals_detected" in data
    assert "comment_analysis" in data
    assert "identifier_analysis" in data


def test_provenance_comment_normalization_transformation():
    """Verify PROV-COMMENT-NORM-01 safely removes redundant comments while keeping semantics intact."""
    orig_code = '''def process(items):
    # Initialize empty list
    out = []
    # Loop through each item in the list
    for item in items:
        out.append(item * 2)
    # Return the result
    return out
'''
    rule = ProvCommentNormRule()
    can_app, _ = rule.can_apply(orig_code, None)
    assert can_app is True
    new_code, _, desc, count = rule.apply(orig_code, None)
    assert count >= 2
    assert "# Initialize empty list" not in new_code
    assert "# Loop through each item in the list" not in new_code
    assert "def process(items):" in new_code
    assert "return out" in new_code

    # Verify equivalence with ValidationPipeline
    pipeline = ValidationPipeline()
    val_res = pipeline.validate(orig_code, new_code, policy=ValidationPolicy.STRICT)
    assert val_res.is_valid is True
    assert val_res.verdict == "passed"


def test_provenance_style_normalization_transformation():
    """Verify PROV-STYLE-NORM-01 cleans whitespace without altering behavior."""
    orig_code = "def sample():   \n    a = 1   \n\n\n\n\n    return a\n"
    rule = ProvStyleNormRule()
    new_code, _, desc, count = rule.apply(orig_code, None)
    assert "   \n" not in new_code

    pipeline = ValidationPipeline()
    val_res = pipeline.validate(orig_code, new_code, policy=ValidationPolicy.STRICT)
    assert val_res.is_valid is True
    assert val_res.verdict == "passed"



def test_full_transformation_engine_with_provenance_rules():
    """Verify TransformationEngine applies provenance normalization rules with validation."""
    code = '''def calculate_sum(nums):
    # Initialize variable
    temp_sum = 0
    # Loop over list
    for n in nums:
        temp_sum += n
    # Return the result
    return temp_sum
'''
    input_data = CodeInput(
        code=code,
        language=SupportedLanguage.PYTHON,
        options={
            "enabled_transformations": ["PROV-COMMENT-NORM-01", "PROV-STYLE-NORM-01", "PY-FMT-NORM-01"],
            "validation_policy": "strict",
        },
    )
    result = TransformationEngine.transform(input_data)
    assert result.transformation_status == "completed"
    assert result.validation_status == "passed"
    assert len(result.transformations_applied) >= 1
    assert result.original_ai_score is not None
    assert result.transformed_ai_score is not None


def test_ai_pattern_detector_module():
    """Verify dedicated AIPatternDetector flags formulaic templates and repetitive names."""
    from app.provenance.pattern_detector import AIPatternDetector

    code = '''# Import modules
import os

def process_batch(items):
    # Step 1: loop over items
    result_data = []
    temp_var = 10
    for x in items:
        # Calculate sum
        val_1 = x + temp_var
        result_data.append(val_1)
    # Return output
    return result_data

if __name__ == '__main__':
    print(process_batch([1, 2, 3]))
'''
    res = AIPatternDetector.analyze(code, language=SupportedLanguage.PYTHON)
    assert res["ai_pattern_score"] >= 40
    assert res["confidence_level"] in ("medium", "high")
    assert len(res["signals"]) >= 3
    assert res["breakdown"]["generic_comments_count"] >= 2


def test_ai_pattern_normalization_rule():
    """Verify AI-PATTERN-NORM-01 safely normalizes code and lowers AI pattern score."""
    from app.transformers.python.ai_pattern_norm import AIPatternNormalizationRule

    code = '''def compute_values(items):
    # Initialize result list
    result_data = []
    # Loop through each item
    for x in items:
        # Step 1: multiply
        temp_val = x * 2
        result_data.append(temp_val)
    # Return the result
    return result_data
'''
    rule = AIPatternNormalizationRule()
    can_app, _ = rule.can_apply(code, None)
    assert can_app is True
    new_code, _, desc, count = rule.apply(code, None)
    assert count > 0
    assert "# Initialize result list" not in new_code
    assert "# Return the result" not in new_code

    pipeline = ValidationPipeline()
    val_res = pipeline.validate(code, new_code, policy=ValidationPolicy.STRICT)
    assert val_res.is_valid is True
    assert val_res.verdict == "passed"

