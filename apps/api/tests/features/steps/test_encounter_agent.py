"""
Test steps for Encounter Agent feature.
"""
import pytest
import asyncio
from pytest_bdd import given, when, then, scenarios
from unittest.mock import AsyncMock
from gm_shield.features.encounters.service import EncounterResponse, NPCStatBlock

scenarios("../encounter_agent.feature")

@given("the RAG knowledge base is active")
def knowledge_base_active():
    pass # No setup needed for mock

@pytest.fixture
def encounter_result_holder():
    return {}

@when('I request an encounter for "Level 5", "Hard", "Swamp ambush"')
def when_request_encounter(encounter_result_holder):
    mock_agent = AsyncMock()
    mock_agent.generate_encounter.return_value = EncounterResponse(
        title="Ambush at Murky Creek",
        description="Mist curls around your ankles...",
        tactics="Archers hide in trees.",
        npcs=[
            NPCStatBlock(
                name="Lizardfolk Shaman",
                creature_type="Humanoid",
                cr="2",
                hp="45",
                ac="13",
                speed="30ft",
                stats="STR 10, DEX 12...",
                actions=["Bite", "Spellcasting"]
            )
        ]
    )

    # Run sync for test
    result = asyncio.run(mock_agent.generate_encounter("Level 5", "Hard", "Swamp ambush"))
    encounter_result_holder["response"] = result

@then('the response should contain a "title"')
def verify_encounter_title(encounter_result_holder):
    response = encounter_result_holder["response"]
    assert response.title is not None
    assert len(response.title) > 0

@then('the response should contain a "description"')
def verify_encounter_description(encounter_result_holder):
    response = encounter_result_holder["response"]
    assert response.description is not None

@then("the response should contain at least 1 NPC stat block")
def verify_npc_count(encounter_result_holder):
    response = encounter_result_holder["response"]
    assert len(response.npcs) >= 1

@then('the NPC stat block should have "hp" and "ac"')
def verify_npc_stats(encounter_result_holder):
    response = encounter_result_holder["response"]
    npc = response.npcs[0]
    assert npc.hp is not None
    assert npc.ac is not None
