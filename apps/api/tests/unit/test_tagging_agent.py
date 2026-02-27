"""
Unit tests for Tagging Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch
from gm_shield.features.notes.service import TaggingService
from gm_shield.features.notes.models import TaggingResponse
from gm_shield.shared.ai.base import AgentResponse
import json

@pytest.fixture
def mock_tagging_agent():
    with patch("gm_shield.features.notes.service.TaggingAgent") as MockAgent:
        agent_instance = MockAgent.return_value
        yield agent_instance

@pytest.mark.asyncio
async def test_tag_note_success(mock_tagging_agent):
    # Setup mocks
    note_content = "Zarathon waits in the Ember Mountains."

    expected_data = {
        "tags": ["NPC", "Location"],
        "keywords": ["Zarathon", "Ember Mountains"],
        "summary": "Zarathon is located in the mountains."
    }

    mock_response = AgentResponse(
        text=json.dumps(expected_data),
        citations=[],
        metadata={"json_data": expected_data}
    )
    mock_tagging_agent.process = AsyncMock(return_value=mock_response)

    service = TaggingService()
    service.agent = mock_tagging_agent

    # Execute
    result = await service.tag_note(note_content)

    # Verify
    assert isinstance(result, TaggingResponse)
    assert result.tags == ["NPC", "Location"]
    assert "Zarathon" in result.keywords

    mock_tagging_agent.process.assert_called_once_with(query=note_content)
