import asyncio
from httpx import AsyncClient
from gm_shield.main import app

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        update_payload = {
            "title": "Session 1 - Revised",
            "content": "Updated content with #Faction clues",
            "tags": ["session"],
            "session_id": "session-1",
            "frontmatter": {"weather": "rain", "session_id": "session-1"},
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
        res = await ac.put("/api/v1/notes/1", json=update_payload)
        print(res.json())

asyncio.run(test())
