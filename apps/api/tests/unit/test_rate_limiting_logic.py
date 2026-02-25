import time
import pytest
from unittest.mock import MagicMock
from gm_shield.shared.middleware.rate_limit import RateLimitMiddleware

class MockSettings:
    RATELIMIT_DEFAULT = 2

@pytest.fixture
def mock_settings(monkeypatch):
    mock = MockSettings()
    monkeypatch.setattr("gm_shield.shared.middleware.rate_limit.settings", mock)
    return mock

@pytest.mark.asyncio
async def test_rate_limit_logic(mock_settings):
    app = MagicMock()
    middleware = RateLimitMiddleware(app)

    # Mock request
    request = MagicMock()
    request.client.host = "127.0.0.1"

    async def call_next(req):
        return "OK"

    # First request
    res = await middleware.dispatch(request, call_next)
    assert res == "OK"

    # Second request
    res = await middleware.dispatch(request, call_next)
    assert res == "OK"

    # Third request - should return JSONResponse with 429
    res = await middleware.dispatch(request, call_next)
    assert res.status_code == 429
