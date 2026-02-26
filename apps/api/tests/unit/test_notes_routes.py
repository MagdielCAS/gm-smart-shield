"""Unit tests for Notes HTTP routes and CRUD behaviour."""

from datetime import datetime


def test_notes_crud_flow(client):
    """Create, list, get, update, and delete a note through the API."""
    create_payload = {
        "title": "Session 1",
        "content": "# Recap\nThe heroes met in a tavern.",
        "tags": ["session", "recap"],
        "campaign_id": "dragon-heist",
        "frontmatter": {"mood": "mysterious"},
    }

    create_response = client.post("/api/v1/notes", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    note_id = created["id"]

    assert created["title"] == create_payload["title"]
    assert created["content"] == create_payload["content"]
    assert set(created["tags"]) == {"session", "recap"}
    assert created["frontmatter"]["campaign_id"] == "dragon-heist"
    assert created["frontmatter"]["mood"] == "mysterious"
    assert len(created["links"]) == 2

    list_response = client.get("/api/v1/notes")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == note_id

    get_response = client.get(f"/api/v1/notes/{note_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == note_id
    original_updated_at = datetime.fromisoformat(fetched["updated_at"])

    update_payload = {
        "title": "Session 1 - Revised",
        "content": "Updated content",
        "tags": ["session"],
        "session_id": "session-1",
        "frontmatter": {"weather": "rain"},
    }

    update_response = client.put(f"/api/v1/notes/{note_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Session 1 - Revised"
    assert updated["frontmatter"]["session_id"] == "session-1"
    assert updated["frontmatter"]["weather"] == "rain"
    assert updated["tags"] == ["session"]
    assert datetime.fromisoformat(updated["updated_at"]) >= original_updated_at

    delete_response = client.delete(f"/api/v1/notes/{note_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/notes/{note_id}")
    assert missing_response.status_code == 404
