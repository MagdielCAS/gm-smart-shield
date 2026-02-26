from unittest.mock import AsyncMock, patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from gm_shield.shared.llm import config as llm_config


@scenario("../llm_health.feature", "System check returns ready when all models are available")
def test_system_check_ready():
    pass


@pytest.fixture
def context():
    return {}


@given("Ollama is running and models are available")
def ollama_running(context):
    patcher = patch("gm_shield.features.health.routes.get_llm_client")
    mock_get_client = patcher.start()
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client

    # Mock list_models to return all required models
    mock_client.list_models.return_value = [
        {"name": llm_config.MODEL_QUERY},
        {"name": llm_config.MODEL_REFERENCE_SMART},
        {"name": llm_config.MODEL_ENCOUNTER},
    ]

    context["patcher"] = patcher


@when(parsers.parse('I GET "{endpoint}"'))
def get_endpoint(client, context, endpoint):
    response = client.get(endpoint)
    context["response"] = response


@then("the response status code should be 200")
def check_status_code(context):
    assert context["response"].status_code == 200


@then(parsers.parse('the response status field should be "{status}"'))
def check_status_field(context, status):
    data = context["response"].json()
    if "patcher" in context:
        context["patcher"].stop()
    assert data["status"] == status
