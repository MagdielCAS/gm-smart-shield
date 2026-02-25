import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gm_shield.shared.middleware.rate_limit import RateLimitMiddleware
from unittest.mock import patch

def test_rate_limiting():
    app = FastAPI()

    # Use patch to mock the settings within the context of this test
    with patch("gm_shield.shared.middleware.rate_limit.settings") as mock_settings:
        mock_settings.RATELIMIT_DEFAULT = 2
        app.add_middleware(RateLimitMiddleware)

        @app.get("/")
        def read_root():
            return {"Hello": "World"}

        # We need to make sure the client uses the app with the middleware configured with mock_settings
        client = TestClient(app)

        # First request - OK
        response = client.get("/")
        assert response.status_code == 200

        # Second request - OK
        response = client.get("/")
        assert response.status_code == 200

        # Third request - Should be rate limited
        response = client.get("/")
        assert response.status_code == 429
        assert response.json() == {"detail": "Rate limit exceeded. Please try again later."}
