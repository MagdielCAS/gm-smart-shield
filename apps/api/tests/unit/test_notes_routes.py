"""Unit tests for Notes HTTP routes and CRUD behaviour."""

from datetime import datetime


def test_notes_crud_flow(client):
    """Create, list, get, update, and delete a note through the API."""
    create_payload = {
        "title": "Session 1",
        "content": "---\nlocation: Waterdeep\n---\n# Recap\nThe heroes met in a tavern with #Harper allies.",
        "tags": ["session", "recap", "recap"],
        "campaign_id": "dragon-heist",
        "frontmatter": {"mood": "mysterious"},
    }

    create_response = client.post("/api/v1/notes", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    note_id = created["id"]

    assert created["title"] == create_payload["title"]
    assert created["content"] == "# Recap\nThe heroes met in a tavern with #Harper allies."
    assert "session" in created["tags"]
    assert "recap" in created["tags"]
    assert "harper" in created["tags"]
    assert len(created["tags"]) == len(set(created["tags"]))
    assert created["frontmatter"]["campaign_id"] == "dragon-heist"
    assert created["frontmatter"]["mood"] == "mysterious"
    assert created["frontmatter"]["location"] == "Waterdeep"
    assert created["metadata"]["word_count"] > 0
    assert len(created["links"]) == len(created["tags"])

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
    original_created_at = datetime.fromisoformat(fetched["created_at"])

    update_payload = {
        "title": "Session 1 - Revised",
        "content": "Updated content with #Faction clues",
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
    assert "session" in updated["tags"]
    assert "faction" in updated["tags"]
    assert len(updated["tags"]) == len(set(updated["tags"]))
    assert datetime.fromisoformat(updated["updated_at"]) >= original_updated_at
    assert datetime.fromisoformat(updated["created_at"]) == original_created_at


    second_update_payload = {
        "title": "Session 1 - Final",
        "content": "Final content",
        "tags": ["final"],
    }
    second_update_response = client.put(f"/api/v1/notes/{note_id}", json=second_update_payload)
    assert second_update_response.status_code == 200
    second_updated = second_update_response.json()
    assert "final" in second_updated["tags"]
    assert "session" not in second_updated["tags"]
    assert "faction" not in second_updated["tags"]

    delete_response = client.delete(f"/api/v1/notes/{note_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/notes/{note_id}")
    assert missing_response.status_code == 404
