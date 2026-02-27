"""
Unit tests for Sheet Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gm_shield.features.sheets.service import SheetService
from gm_shield.features.sheets.models import SheetTemplateResponse
from gm_shield.shared.ai.base import AgentResponse

@pytest.fixture
def mock_sheet_agent():
    with patch("gm_shield.features.sheets.service.SheetAgent") as MockAgent:
        agent_instance = MockAgent.return_value
        yield agent_instance

@pytest.fixture
def mock_query_knowledge():
    with patch("gm_shield.features.sheets.service.query_knowledge") as mock_query:
        yield mock_query

@pytest.mark.asyncio
async def test_generate_template_success(mock_sheet_agent, mock_query_knowledge):
    # Setup mocks
    mock_query_knowledge.return_value = [
        {"content": "Strength measures bodily power.", "metadata": {"source": "phb.pdf", "page": 10}}
    ]

    mock_response = AgentResponse(
        text="---\nname: [Value]\n---\n# Character Sheet",
        citations=[],
        metadata={}
    )
    mock_sheet_agent.process = AsyncMock(return_value=mock_response)

    # Initialize service
    service = SheetService()
    # Manually inject mock agent because __init__ creates a new one
    service.agent = mock_sheet_agent

    # Execute
    result = await service.generate_template("phb.pdf", "D&D 5e")

    # Verify
    assert isinstance(result, SheetTemplateResponse)
    assert result.template_markdown == mock_response.text
    assert "name" in result.frontmatter_schema

    mock_query_knowledge.assert_called_once()
    mock_sheet_agent.process.assert_called_once()

@pytest.mark.asyncio
async def test_generate_template_no_context(mock_sheet_agent, mock_query_knowledge):
    # Setup mocks
    mock_query_knowledge.return_value = []

    mock_response = AgentResponse(
        text="---\nname: [Value]\n---\n# Basic Sheet",
        citations=[],
        metadata={}
    )
    mock_sheet_agent.process = AsyncMock(return_value=mock_response)

    service = SheetService()
    service.agent = mock_sheet_agent

    # Execute
    result = await service.generate_template("phb.pdf", "D&D 5e")

    # Verify
    assert result.template_markdown == mock_response.text
    mock_sheet_agent.process.assert_called_once()
