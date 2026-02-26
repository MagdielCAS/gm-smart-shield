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
        "sources": [
            {
                "source_id": "monster-manual",
                "source_file": "/data/monster-manual.pdf",
                "page_number": 42,
                "chunk_id": "monster-manual_abc123_0",
            }
        ],
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
    assert created["links"][0]["source_id"] == "monster-manual"
    assert created["links"][0]["page_number"] == 42

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
        "sources": [
            {
                "source_id": "dm-guide",
                "source_file": "/data/dm-guide.pdf",
                "page_number": 99,
                "chunk_id": "dm-guide_xyz987_2",
            }
        ],
    }

    update_response = client.put(f"/api/v1/notes/{note_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Session 1 - Revised"
    assert updated["frontmatter"]["session_id"] == "session-1"
    assert updated["frontmatter"]["weather"] == "rain"
    assert "session" in updated["tags"]
    assert "faction" in updated["tags"]
    assert updated["links"][0]["source_id"] == "dm-guide"
    assert updated["links"][0]["page_number"] == 99
    assert len(updated["tags"]) == len(set(updated["tags"]))
    assert datetime.fromisoformat(updated["updated_at"]) >= original_updated_at
    assert datetime.fromisoformat(updated["created_at"]) == original_created_at

    second_update_payload = {
        "title": "Session 1 - Final",
        "content": "Final content",
        "tags": ["final"],
        "sources": [],
    }
    second_update_response = client.put(f"/api/v1/notes/{note_id}", json=second_update_payload)
    assert second_update_response.status_code == 200
    second_updated = second_update_response.json()
    assert "final" in second_updated["tags"]
    assert "session" not in second_updated["tags"]
    assert "faction" not in second_updated["tags"]
    assert second_updated["links"] == []

    delete_response = client.delete(f"/api/v1/notes/{note_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/notes/{note_id}")
    assert missing_response.status_code == 404


def test_note_link_suggestions_endpoint(client, monkeypatch):
    """Suggest source links using mocked Chroma semantic and keyword results."""

    class MockCollection:
        def query(self, query_texts, n_results, include):
            return {
                "ids": [["chunk-1", "chunk-2"]],
                "documents": [["Waterdeep harbor smuggling ring", "Neverwinter politics"]],
                "metadatas": [[{"source": "/data/lore.pdf", "page_number": 5}, {"source": "/data/lore.pdf", "page_number": 10}]],
                "distances": [[0.1, 0.6]],
            }

        def get(self, include):
            return {
                "ids": ["chunk-3"],
                "documents": ["Waterdeep guild conflict"],
                "metadatas": [{"source": "/data/factions.pdf", "page_number": 18}],
            }

    class MockClient:
        def get_collection(self, name):
            assert name == "knowledge_base"
            return MockCollection()

    monkeypatch.setattr("gm_shield.features.notes.service.get_chroma_client", lambda: MockClient())

    create_response = client.post(
        "/api/v1/notes",
        json={
            "title": "Session 2",
            "content": "The party investigated Waterdeep guild politics and a smuggling ring.",
            "tags": ["session"],
            "sources": [],
        },
    )
    assert create_response.status_code == 201
    note_id = create_response.json()["id"]

    suggest_response = client.post(f"/api/v1/notes/{note_id}/links/suggest", json={"limit": 2})
    assert suggest_response.status_code == 200
    payload = suggest_response.json()
    assert payload["note_id"] == note_id
    assert len(payload["suggestions"]) == 2
    assert payload["suggestions"][0]["chunk_id"] == "chunk-1"
    assert payload["suggestions"][0]["page_number"] == 5
