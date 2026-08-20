"""Pytest configuration and fixtures for CodeSanitize backend tests."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client fixture reused across the test session."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client():
    """Asynchronous HTTP test client fixture."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
