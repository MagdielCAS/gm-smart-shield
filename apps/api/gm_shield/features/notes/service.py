"""
Tagging Service — Orchestrates note tagging.

Uses the Tagging Agent to extract keywords and optionally
links them to the knowledge base (future enhancement).
"""

from typing import Dict, Any, List
from gm_shield.features.notes.agent import TaggingAgent
from gm_shield.features.notes.models import TaggingResponse
from gm_shield.core.logging import get_logger
import json

logger = get_logger(__name__)


class TaggingService:
    """
    Service for auto-tagging.
    """

    def __init__(self):
        self.agent = TaggingAgent()

    async def tag_note(self, content: str) -> TaggingResponse:
        """
        Analyzes note content and returns tags.
        """
        logger.info("tagging_service_tag")

        # 1. Tagging Agent
        response = await self.agent.process(query=content)

        # 2. Parse Response
        try:
            data = response.metadata.get("json_data")
            if not data:
                data = json.loads(response.text)

            tags = data.get("tags", [])
            keywords = data.get("keywords", [])

            # Future: Search ChromaDB for these keywords to find suggested links
            # For now, we return empty links
            suggested_links = []

            return TaggingResponse(
                tags=tags,
                keywords=keywords,
                suggested_links=suggested_links,
                metadata=response.metadata
            )
        except Exception as e:
            logger.error("tagging_parsing_failed", error=str(e))
            return TaggingResponse(
                tags=[],
                keywords=[],
                suggested_links=[],
                metadata={"error": str(e), "raw_output": response.text}
            )

# Singleton
_tagging_service = TaggingService()

def get_tagging_service() -> TaggingService:
    return _tagging_service
