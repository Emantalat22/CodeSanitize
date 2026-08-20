"""Unit tests for health check endpoints and core schema validation."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.models.schemas import (
    CodeInput,
    HealthResponse,
    SupportedLanguage,
)


def test_health_endpoint(client: TestClient):
    """Test that GET /api/health returns 200 and expected status payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "CodeSanitize"
    assert data["version"] == "0.1.0"
    assert "environment" in data
    assert "timestamp" in data

    # Verify Pydantic parsing succeeds
    health_model = HealthResponse(**data)
    assert health_model.status == "ok"


def test_root_endpoint(client: TestClient):
    """Test that GET / returns application information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CodeSanitize"
    assert data["health"] == "/api/health"


def test_list_languages_endpoint(client: TestClient):
    """Test that GET /api/languages lists supported languages."""
    response = client.get("/api/languages")
    assert response.status_code == 200
    languages = response.json()
    assert isinstance(languages, list)
    assert len(languages) > 0

    language_ids = [item["id"] for item in languages]
    assert "python" in language_ids
    assert "javascript" in language_ids
    assert "typescript" in language_ids
    assert "java" in language_ids
    assert "cpp" in language_ids


def test_validate_endpoint_returns_200(client: TestClient):
    """Verify that POST /api/validate runs validation and returns HTTP 200."""
    payload = {
        "original_code": "def hello(): pass\n",
        "transformed_code": "def hello(): pass\n",
        "language": "python",
    }

    validate_res = client.post("/api/validate", json=payload)
    assert validate_res.status_code == 200
    data = validate_res.json()
    assert data["is_valid"] is True
    assert data["verdict"] == "passed"




def test_code_input_schema_validation():
    """Verify that CodeInput model properly validates inputs and rejects invalid language enums."""
    valid_input = CodeInput(
        code="print('test')",
        language=SupportedLanguage.PYTHON,
        filename="test.py",
    )
    assert valid_input.language == SupportedLanguage.PYTHON

    with pytest.raises(ValidationError):
        # Invalid language string should raise ValidationError
        CodeInput(code="pass", language="unsupported_lang_xyz")  # type: ignore


@pytest.mark.asyncio
async def test_async_health_endpoint(async_client):
    """Test asynchronous client execution against health endpoint."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
