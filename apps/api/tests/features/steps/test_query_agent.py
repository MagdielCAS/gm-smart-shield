from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario("../query_agent.feature", "Stream a simple answer")
def test_stream_answer():
    pass


@pytest.fixture
def context():
    return {}


@given("the knowledge base is ready")
def knowledge_ready(context):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_mcp_cm(*args, **kwargs):
        yield []

    # Patch the real load_mcp_tools since it's imported inline in the method
    patcher_mcp = patch("langchain_mcp_adapters.tools.load_mcp_tools", new=mock_mcp_cm)
    patcher_mcp.start()

    # Mock create_deep_agent
    patcher_agent = patch("gm_shield.features.chat.service.create_deep_agent")
    mock_create_agent = patcher_agent.start()

    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    # Mock astream_events to yield SSE-like events
    async def mock_astream_events(*args, **kwargs):
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": MagicMock(content="Part 1")},
        }
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": MagicMock(content="Part 2")},
        }

    mock_agent.astream_events = mock_astream_events

    context["patchers"] = [patcher_mcp, patcher_agent]


@when(parsers.parse('I ask "{question}"'))
def ask_question(client, context, question):
    response = client.post("/api/v1/chat/query", json={"query": question})
    context["response"] = response


@then("I should receive a streaming response")
def check_stream(context):
    response = context["response"]
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Part 1" in content
    assert "Part 2" in content

    for p in context.get("patchers", []):
        p.stop()
