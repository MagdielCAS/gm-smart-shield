import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from gm_shield.main import app
from gm_shield.shared.database.sqlite import get_db

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.execute.return_value = None
    return session


@pytest.fixture
def override_get_db(mock_db_session):
    def _get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides = {}


@pytest.fixture
def mock_chroma():
    with patch("gm_shield.features.health.routes.get_chroma_client") as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def mock_httpx():
    # Patch the class; the return value of calling it is the async context manager instance.
    with patch("httpx.AsyncClient") as mock:
        yield mock


def test_health_heartbeat():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_health_status_all_ok(override_get_db, mock_chroma, mock_httpx):
    # Build an AsyncMock that acts as the httpx.AsyncClient context manager instance.
    instance = AsyncMock()
    mock_httpx.return_value = instance
    instance.__aenter__.return_value = instance

    # Mock the Ollama /api/tags response.
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "granite4:latest"},
            {"name": "gemma3:12b-it-qat"},
        ]
    }
    instance.get.return_value = response_mock

    # Route is now mounted under /api/v1 prefix.
    response = client.get("/api/v1/health/status")

    if response.status_code != 200 or not response.json().get("ollama"):
        print(f"DEBUG Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["database"] is True
    assert data["chroma"] is True
    assert data["ollama"] is True
    assert data["ollama_models"]["llama3.2:3b"] is True
    assert not data["errors"]


def test_health_status_missing_model(override_get_db, mock_chroma, mock_httpx):
    instance = AsyncMock()
    mock_httpx.return_value = instance
    instance.__aenter__.return_value = instance

    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            # granite4 deliberately omitted to test the missing-model error path.
            {"name": "gemma3:12b-it-qat"},
        ]
    }
    instance.get.return_value = response_mock

    response = client.get("/api/v1/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ollama_models"]["granite4:latest"] is False
    assert any(
        "Missing required model: granite4:latest" in err for err in data["errors"]
    )


def test_health_status_db_fail(mock_chroma, mock_httpx):
    # Override the DB dependency to simulate a connection failure.
    def _get_db_fail():
        session = MagicMock()
        session.execute.side_effect = Exception("DB Connection Failed")
        yield session

    app.dependency_overrides[get_db] = _get_db_fail

    # Ollama is healthy for this test — only the DB fails.
    instance = AsyncMock()
    mock_httpx.return_value = instance
    instance.__aenter__.return_value = instance
    instance.get.return_value.status_code = 200
    instance.get.return_value.json.return_value = {"models": []}

    response = client.get("/api/v1/health/status")
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["database"] is False
    assert any("SQLite error" in err for err in data["errors"])
