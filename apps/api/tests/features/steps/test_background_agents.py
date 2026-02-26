"""
Test steps for Background Agents feature.
"""
import pytest
import asyncio
from pytest_bdd import given, when, then, scenarios
from unittest.mock import AsyncMock, MagicMock
from gm_shield.features.knowledge.models import CharacterSheetTemplate, QuickReference, KnowledgeSource
from gm_shield.features.knowledge.tasks import run_sheet_extraction, run_reference_extraction

scenarios("../background_agents.feature")

# Note: We are using a sync wrapper for async steps to avoid pytest-bdd/asyncio conflict issues
# in this specific environment configuration.

@pytest.fixture
def sheet_source_id(db_session):
    source = KnowledgeSource(
        file_path="/tmp/DungeonMasterGuide.pdf",
        status="completed",
        current_step="Done"
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source.id

@given('the knowledge base contains a file "DungeonMasterGuide.pdf"')
def given_sheet_source(sheet_source_id):
    return sheet_source_id

@when("the ingestion background pipeline task completes")
def run_sheet_extraction_task(db_session, sheet_source_id, monkeypatch):
    source_id = sheet_source_id

    # Mock extract_text_from_file located in gm_shield.features.knowledge.service
    mock_extract = MagicMock(return_value="Character Name: ____________\nClass: __________ Level: ___\nSTR: __ DEX: __")
    monkeypatch.setattr("gm_shield.features.knowledge.service.extract_text_from_file", mock_extract)

    # Mock SheetAgent
    mock_agent = AsyncMock()
    from gm_shield.features.knowledge.agents.sheet import CharacterSheetSchema
    mock_agent.extract_template.return_value = CharacterSheetSchema(
        system_name="D&D 5e",
        template_name="Standard",
        sections={"Attributes": ["STR", "DEX"]}
    )

    # Patch the Agent class instantiation in tasks.py
    monkeypatch.setattr("gm_shield.features.knowledge.tasks.SheetAgent", lambda: mock_agent)

    # Patch SessionLocal to use our test session
    monkeypatch.setattr("gm_shield.features.knowledge.tasks.SessionLocal", lambda: db_session)

    # Run the async task synchronously for testing
    asyncio.run(run_sheet_extraction(source_id))

@then("a CharacterSheetTemplate should be stored in the database for that source")
def verify_sheet_template_exists(db_session, sheet_source_id):
    template = db_session.query(CharacterSheetTemplate).filter_by(source_id=sheet_source_id).first()
    assert template is not None

@then('the template should contain "system" and "template_schema"')
def verify_sheet_template_content(db_session, sheet_source_id):
    template = db_session.query(CharacterSheetTemplate).filter_by(source_id=sheet_source_id).first()
    assert template.system == "D&D 5e"
    assert "Attributes" in template.template_schema


# Reference Agent Steps

@pytest.fixture
def ref_source_id(db_session):
    source = KnowledgeSource(
        file_path="/tmp/Spells.txt",
        status="completed",
        current_step="Done"
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source.id

@given('the knowledge base contains a file "Spells.txt"')
def given_ref_source(ref_source_id):
    return ref_source_id

@when("the reference extraction task runs")
def run_reference_extraction_task(db_session, ref_source_id, monkeypatch):
    source_id = ref_source_id

    # Mock extract_text_from_file located in gm_shield.features.knowledge.service
    mock_extract = MagicMock(return_value="Fireball: Level 3 Evocation. 8d6 fire damage.")
    monkeypatch.setattr("gm_shield.features.knowledge.service.extract_text_from_file", mock_extract)

    mock_agent = AsyncMock()
    from gm_shield.features.knowledge.agents.reference import ReferenceItem
    mock_agent.extract_references.return_value = [
        ReferenceItem(name="Fireball", category="Spell", description="8d6 fire", tags=["Evocation"])
    ]

    monkeypatch.setattr("gm_shield.features.knowledge.tasks.ReferenceAgent", lambda: mock_agent)
    monkeypatch.setattr("gm_shield.features.knowledge.tasks.SessionLocal", lambda: db_session)

    asyncio.run(run_reference_extraction(source_id))

@then('the system should identify "Fireball" as a "Spell"')
def verify_reference_extraction(db_session, ref_source_id):
    ref = db_session.query(QuickReference).filter_by(source_id=ref_source_id, name="Fireball").first()
    assert ref is not None
    assert ref.category == "Spell"

@then("a QuickReference record should be created")
def verify_reference_count(db_session, ref_source_id):
    count = db_session.query(QuickReference).filter_by(source_id=ref_source_id).count()
    assert count > 0
