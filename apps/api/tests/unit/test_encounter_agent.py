"""
Unit tests for Encounter Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch
from gm_shield.features.encounters.service import EncounterService
from gm_shield.features.encounters.models import EncounterResponse
from gm_shield.shared.ai.base import AgentResponse
import json

@pytest.fixture
def mock_encounter_agent():
    with patch("gm_shield.features.encounters.service.EncounterAgent") as MockAgent:
        agent_instance = MockAgent.return_value
        yield agent_instance

@pytest.fixture
def mock_query_knowledge():
    with patch("gm_shield.features.encounters.service.query_knowledge") as mock_query:
        yield mock_query

@pytest.mark.asyncio
async def test_generate_encounter_success(mock_encounter_agent, mock_query_knowledge):
    # Setup mocks
    mock_query_knowledge.return_value = [
        {"content": "Goblins are small humanoids.", "metadata": {"source": "mm.pdf", "page": 40}}
    ]

    expected_data = {
        "title": "Goblin Ambush",
        "description": "Three goblins jump out.",
        "tactics": "They shoot and hide.",
        "npc_stats": [{"name": "Goblin", "hp": "7"}],
        "loot": "10 gold pieces."
    }

    mock_response = AgentResponse(
        text=json.dumps(expected_data),
        citations=[],
        metadata={"json_data": expected_data}
    )
    mock_encounter_agent.process = AsyncMock(return_value=mock_response)

    service = EncounterService()
    service.agent = mock_encounter_agent

    # Execute
    result = await service.generate_encounter(1, "Forest", "Easy")

    # Verify
    assert isinstance(result, EncounterResponse)
    assert result.title == "Goblin Ambush"
    assert len(result.npc_stats) == 1

    mock_query_knowledge.assert_called_once()
    mock_encounter_agent.process.assert_called_once()

@pytest.mark.asyncio
async def test_generate_encounter_json_fallback(mock_encounter_agent, mock_query_knowledge):
    # Test fallback when metadata doesn't contain json_data but text does
    mock_query_knowledge.return_value = []

    expected_data = {
        "title": "Dragon Fight",
        "description": "A dragon appears.",
        "tactics": "Breath weapon.",
        "npc_stats": [],
        "loot": "None"
    }

    mock_response = AgentResponse(
        text=json.dumps(expected_data),
        citations=[],
        metadata={} # Missing json_data
    )
    mock_encounter_agent.process = AsyncMock(return_value=mock_response)

    service = EncounterService()
    service.agent = mock_encounter_agent

    # Execute
    result = await service.generate_encounter(10, "Mountain", "Hard")

    # Verify
    assert result.title == "Dragon Fight"
