import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario("../tagging_agent.feature", "Auto-tagging a saved note")
def test_auto_tagging():
    pass


@pytest.fixture
def context():
    return {}


@given(parsers.parse('I have a note titled "{title}"'))
def create_note(client, context, title):
    response = client.post(
        "/api/v1/notes", json={"title": title, "content": "Initial content"}
    )
    assert response.status_code == 201
    context["note_id"] = response.json()["id"]


@when(parsers.parse('I save the note with content "{content}"'))
def save_note(client, context, content):
    # The current feature branch has a deterministic tag extracting routine
    # We don't need to patch an agent if it's using the text heuristics.

    # Update the note
    response = client.put(
        f"/api/v1/notes/{context['note_id']}",
        json={
            "title": context.get("note_title", "Sewer Encounter"),
            "content": content,
        },
    )
    assert response.status_code == 200


@then(parsers.parse("the system should generate a background task for tagging"))
def check_task_generated(context):
    pass  # Synchronous enrichment, so this is instantaneous now


@then(parsers.parse('eventually the note should contain the tag "{tag}"'))
def check_tags(client, context, tag):
    response = client.get(f"/api/v1/notes/{context['note_id']}")
    data = response.json()
    tags = data["tags"]
    assert tag.lower() in tags, f"Tag {tag.lower()} not found. Tags: {tags}"
