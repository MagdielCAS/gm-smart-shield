import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from gm_shield.main import app
from gm_shield.features.health.routes import HealthStatus
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
    # We patch the class. The return value of calling the class is the instance.
    with patch("httpx.AsyncClient") as mock:
        yield mock

def test_health_heartbeat():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_health_status_all_ok(override_get_db, mock_chroma, mock_httpx):
    # Prepare the instance mock
    # We want the instance to be an AsyncMock so its methods are async
    instance = AsyncMock()
    mock_httpx.return_value = instance

    # When using 'async with', it calls __aenter__
    # instance.__aenter__ should return the instance (or whatever 'as client' expects)
    # Since instance is AsyncMock, __aenter__ is already async.
    # We set its return value to the instance itself.
    instance.__aenter__.return_value = instance

    # Mock the response
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "granite4:latest"},
            {"name": "gemma3:12b-it-qat"}
        ]
    }

    # Set the return value of get(). Since instance is AsyncMock, instance.get is AsyncMock.
    instance.get.return_value = response_mock

    response = client.get("/health/status")

    # Debug info
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
            # granite4 missing
            {"name": "gemma3:12b-it-qat"}
        ]
    }
    instance.get.return_value = response_mock

    response = client.get("/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ollama_models"]["granite4:latest"] is False
    assert any("Missing required model: granite4:latest" in err for err in data["errors"])

def test_health_status_db_fail(mock_chroma, mock_httpx):
    # Override DB to fail
    def _get_db_fail():
        session = MagicMock()
        session.execute.side_effect = Exception("DB Connection Failed")
        yield session

    app.dependency_overrides[get_db] = _get_db_fail

    # Mock Ollama OK
    instance = AsyncMock()
    mock_httpx.return_value = instance
    instance.__aenter__.return_value = instance
    instance.get.return_value.status_code = 200
    instance.get.return_value.json.return_value = {"models": []}

    response = client.get("/health/status")
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["database"] is False
    assert any("SQLite error" in err for err in data["errors"])
