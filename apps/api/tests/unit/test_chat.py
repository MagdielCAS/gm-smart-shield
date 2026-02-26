import pytest
from unittest.mock import patch, AsyncMock
from gm_shield.features.chat.agent import QueryAgent
from gm_shield.features.chat.service import ChatService
from gm_shield.shared.ai.base import AgentResponse


@pytest.mark.asyncio
async def test_query_agent_process():
    with patch("gm_shield.features.chat.agent.OllamaAgent"):
        agent = QueryAgent()
        # Mock the LCEL chain instead of the raw LLM
        agent.chain = AsyncMock()
        agent.chain.ainvoke.return_value = "Test answer"

        response = await agent.process("Hello?", context="Mock context")

        assert isinstance(response, AgentResponse)
        assert response.text == "Test answer"
        agent.chain.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_chat_service_get_response():
    with patch("gm_shield.features.chat.service.query_knowledge") as mock_query:
        with patch("gm_shield.features.chat.service.QueryAgent") as mock_agent_class:
            # Mock knowledge retrieval
            mock_query.return_value = [
                {
                    "content": "Rules for fire",
                    "metadata": {"source": "rules.pdf"},
                    "score": 0.1,
                }
            ]

            # Mock agent
            mock_agent = AsyncMock()
            mock_agent.process.return_value = AgentResponse(
                text="Fire is hot", citations=[]
            )
            mock_agent_class.return_value = mock_agent

            service = ChatService()
            response = await service.get_response("Tell me about fire")

            assert response.text == "Fire is hot"
            mock_query.assert_called_once_with("Tell me about fire", top_k=5)
            mock_agent.process.assert_called_once()
            args, kwargs = mock_agent.process.call_args
            assert "Rules for fire" in kwargs["context"]
