"""
Notes feature — Tagging Agent.

Extracts entities and keywords from note content.
"""

import json
from typing import List

from gm_shield.core.logging import get_logger
from gm_shield.shared.llm import config as llm_config
from gm_shield.shared.llm.agent import BaseAgent

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an RPG assistant. Your job is to extract relevant tags and entities (NPCs, Locations, Items, Monsters) from the user's note.
Output ONLY a JSON list of strings. Do not output anything else.
Example: ["Goblin", "Dark Forest", "Sword of Light"]
"""


class TaggingAgent(BaseAgent):
    """
    Agent that extracts tags from text.
    """

    def __init__(self):
        super().__init__(model=llm_config.MODEL_TAGGING, system_prompt=SYSTEM_PROMPT)

    async def extract_tags(self, content: str) -> List[str]:
        """
        Extract tags from the given content.

        Args:
            content: The note content.

        Returns:
            A list of extracted tags.
        """
        if not content.strip():
            return []

        try:
            # We enforce JSON format
            response = await self.generate(content, format="json")
            data = json.loads(response)

            # Expecting a list directly, or a dict with a list
            if isinstance(data, list):
                return [str(tag) for tag in data]
            elif isinstance(data, dict):
                # Try to find a list value, or if keys are tags?
                # Usually with format="json", strict schema is better, but Ollama "json" mode
                # just enforces valid JSON.
                # If model outputs {"tags": [...]}, we handle it.
                for val in data.values():
                    if isinstance(val, list):
                        return [str(tag) for tag in val]

            return []
        except Exception as e:
            logger.error("tagging_failed", error=str(e))
            return []
