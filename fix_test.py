import json

update_payload = {
    "title": "Session 1 - Revised",
    "content": "Updated content with #Faction clues",
    "tags": ["session"],
    "frontmatter": {
        "weather": "rain",
        "session_id": "session-1"
    },
    "sources": [
        {
            "tag": "rules",
            "source_id": "dm-guide",
            "source_file": "/data/dm-guide.pdf",
            "page_number": 99,
            "chunk_id": "dm-guide_xyz987_2",
        }
    ],
}
print(json.dumps(update_payload, indent=2))
