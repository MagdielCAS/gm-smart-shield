"""
Unit tests for Reference Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch
from gm_shield.features.references.service import ReferenceService
from gm_shield.features.references.models import ReferenceResponse
from gm_shield.shared.ai.base import AgentResponse

@pytest.fixture
def mock_reference_agent():
    with patch("gm_shield.features.references.service.ReferenceAgent") as MockAgent:
        agent_instance = MockAgent.return_value
        yield agent_instance

@pytest.fixture
def mock_query_knowledge():
    with patch("gm_shield.features.references.service.query_knowledge") as mock_query:
        yield mock_query

@pytest.mark.asyncio
async def test_generate_reference_success(mock_reference_agent, mock_query_knowledge):
    # Setup mocks
    mock_query_knowledge.return_value = [
        {"content": "Fireball deals 8d6 damage.", "metadata": {"source": "phb.pdf", "page": 100}}
    ]

    mock_response = AgentResponse(
        text="# Fireball\nDeals 8d6 fire damage.",
        citations=[],
        metadata={}
    )
    mock_reference_agent.process = AsyncMock(return_value=mock_response)

    service = ReferenceService()
    service.agent = mock_reference_agent

    # Execute
    result = await service.generate_reference("Spells", "phb.pdf")

    # Verify
    assert isinstance(result, ReferenceResponse)
    assert result.content == mock_response.text
    assert result.category == "Spells"

    mock_query_knowledge.assert_called_once()
    mock_reference_agent.process.assert_called_once()
