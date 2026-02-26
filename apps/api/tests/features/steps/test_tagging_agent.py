import time
from unittest.mock import AsyncMock, patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from sqlalchemy.orm import sessionmaker


@scenario("../tagging_agent.feature", "Auto-tagging a saved note")
def test_auto_tagging():
    pass


@pytest.fixture
def context():
    return {}


@pytest.fixture(autouse=True)
def patch_session_local(db_session):
    """
    Ensure the background task uses the same database connection as the test.
    This is crucial for SQLite in-memory databases.
    """
    # Get the connection/engine from the test session
    bind = db_session.get_bind()

    # Create a factory that binds to the same engine
    TestSession = sessionmaker(bind=bind)

    # Patch the SessionLocal imported in service.py
    # Since service.py does `from ... import SessionLocal`, we must patch it there.
    with patch("gm_shield.features.notes.service.SessionLocal", side_effect=TestSession):
        yield


@given(parsers.parse('I have a note titled "{title}"'))
def create_note(client, context, title):
    response = client.post(
        "/api/v1/notes/", json={"title": title, "content": "Initial content"}
    )
    assert response.status_code == 201
    context["note_id"] = response.json()["id"]


@when(parsers.parse('I save the note with content "{content}"'))
def save_note(client, context, content):
    # Patch TaggingAgent to return deterministic tags
    patcher = patch("gm_shield.features.notes.service.TaggingAgent")
    MockAgent = patcher.start()
    mock_instance = AsyncMock()
    MockAgent.return_value = mock_instance
    mock_instance.extract_tags.return_value = ["Wererat", "Encounter"]
    context["patcher"] = patcher

    # Update the note
    response = client.put(
        f"/api/v1/notes/{context['note_id']}", json={"content": content}
    )
    assert response.status_code == 200


@then("the system should generate a background task for tagging")
def check_task_generated(context):
    pass  # implicit


@then(parsers.parse('eventually the note should contain the tag "{tag}"'))
def check_tags(client, context, tag):
    # Poll for tags
    time.sleep(0.5)

    for _ in range(10): # Increased retries
        response = client.get(f"/api/v1/notes/{context['note_id']}")
        data = response.json()
        tags = [t["tag"] for t in data["tags"]]
        if tag in tags:
            return
        time.sleep(0.2)

    pytest.fail(f"Tag {tag} not found. Tags: {tags}")


@pytest.fixture(autouse=True)
def teardown_mocks(context):
    yield
    if "patcher" in context:
        context["patcher"].stop()
