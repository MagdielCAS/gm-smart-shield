import requests

payload = {
  "title": "Session 1 - Revised",
  "content": "Updated content with #Faction clues",
  "tags": [
    "session"
  ],
  "session_id": "session-1",
  "frontmatter": {
    "weather": "rain"
  },
  "sources": [
    {
      "tag": "rules",
      "source_id": "dm-guide",
      "source_file": "/data/dm-guide.pdf",
      "page_number": 99,
      "chunk_id": "dm-guide_xyz987_2"
    }
  ]
}

print(requests.put("http://localhost:8000/api/v1/notes/1", json=payload).text)
