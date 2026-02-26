from unittest.mock import AsyncMock, MagicMock, patch

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
    # Mock get_embedding_model (Sync)
    patcher_embed = patch("gm_shield.features.chat.service.get_embedding_model")
    mock_embed = patcher_embed.start()
    mock_model = MagicMock()
    mock_embed.return_value = mock_model
    # encode returns an object with tolist()
    mock_array = MagicMock()
    mock_array.tolist.return_value = [0.1, 0.2]
    mock_model.encode.return_value = mock_array

    # Mock get_chroma_client (Sync)
    patcher_chroma = patch("gm_shield.features.chat.service.get_chroma_client")
    mock_chroma = patcher_chroma.start()
    mock_client = MagicMock()
    mock_chroma.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    # Mock collection.query
    mock_collection.query.return_value = {
        "documents": [["Chunk 1"]],
        "metadatas": [[{"source": "test.pdf"}]],
    }

    # Mock OllamaClient via BaseAgent (Sync getter, async methods)
    patcher_llm = patch("gm_shield.shared.llm.agent.get_llm_client")
    mock_llm = patcher_llm.start()
    mock_llm_client = MagicMock()
    mock_llm.return_value = mock_llm_client

    # Mock stream generator
    async def async_gen(*args, **kwargs):
        yield "Part 1"
        yield "Part 2"

    mock_llm_client.stream.side_effect = async_gen

    context["patchers"] = [patcher_embed, patcher_chroma, patcher_llm]


@when(parsers.parse('I ask "{question}"'))
def ask_question(client, context, question):
    # Using TestClient with stream=True
    response = client.post("/api/v1/chat/query", json={"query": question})
    context["response"] = response


@then("I should receive a streaming response")
def check_stream(context):
    response = context["response"]
    assert response.status_code == 200
    # Consuming stream content
    content = response.content.decode("utf-8")
    assert "Part 1" in content
    assert "Part 2" in content

    # Cleanup
    for p in context.get("patchers", []):
        p.stop()
