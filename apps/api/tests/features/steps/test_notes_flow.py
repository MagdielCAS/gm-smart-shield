"""BDD steps for the Notes API create/update/tag/link flow."""

from pytest_bdd import given, scenario, then, when


@scenario("../notes_flow.feature", "Create, update, and enrich note with tags and source links")
def test_notes_create_update_tag_link_flow() -> None:
    """Run the end-to-end notes create/update/tag/link flow scenario."""


@given("the API is running for notes", target_fixture="notes_context")
def notes_context(client):
    """Provide a mutable context dictionary scoped to the notes scenario."""
    return {"client": client}


@when("I create a note with markdown frontmatter and hashtags")
def create_note(notes_context) -> None:
    """Create a note and store the created payload for later assertions."""
    response = notes_context["client"].post(
        "/api/v1/notes",
        json={
            "title": "Session 12",
            "content": "---\nlocation: Neverwinter\n---\nThe #Harper contact briefed Mirt.",
            "tags": ["session", "briefing"],
            "campaign_id": "storm-kings-thunder",
            "sources": [],
        },
    )
    assert response.status_code == 201
    notes_context["created"] = response.json()


@when("I update the created note with refined content and source links")
def update_note(notes_context) -> None:
    """Update the created note with additional tags and structured links."""
    note_id = notes_context["created"]["id"]
    response = notes_context["client"].put(
        f"/api/v1/notes/{note_id}",
        json={
            "title": "Session 12 Revised",
            "content": "Mirt and the #LordsAlliance discussed Neverwinter logistics.",
            "tags": ["session", "recap"],
            "session_id": "s12",
            "sources": [
                {
                    "source_id": "sword-coast-guide",
                    "source_file": "/data/sword-coast-guide.pdf",
                    "page_number": 88,
                    "chunk_id": "scag_88_2",
                }
            ],
        },
    )
    assert response.status_code == 200
    notes_context["updated"] = response.json()


@then("the updated note should include merged metadata and extracted tags")
def assert_tags_and_metadata(notes_context) -> None:
    """Verify note metadata merge behaviour and deterministic tag extraction."""
    updated = notes_context["updated"]
    assert updated["frontmatter"]["session_id"] == "s12"
    assert "session" in updated["tags"]
    assert "recap" in updated["tags"]
    assert "lordsalliance" in updated["tags"]
    assert updated["metadata"]["word_count"] > 0


@then("the updated note should expose linked source metadata")
def assert_links(notes_context) -> None:
    """Verify linked source fields survive round-trip persistence."""
    updated = notes_context["updated"]
    assert len(updated["links"]) == 1
    assert updated["links"][0]["source_id"] == "sword-coast-guide"
    assert updated["links"][0]["page_number"] == 88
