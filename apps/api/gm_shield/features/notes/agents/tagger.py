"""
Notes feature — Tagging Agent.

Extracts entities and keywords from note content.
"""

from typing import List
from pydantic import BaseModel, Field

from gm_shield.core.logging import get_logger
from gm_shield.shared.llm import config as llm_config

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an RPG assistant. Your job is to extract relevant tags and entities (NPCs, Locations, Items, Monsters) from the user's note.
Output ONLY a JSON list of strings. Do not output anything else.
Example: ["Goblin", "Dark Forest", "Sword of Light"]
"""


class TagResponse(BaseModel):
    tags: List[str] = Field(description="A list of extracted tags.")


class TaggingAgent:
    """
    Agent that extracts tags from text.
    """

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

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
            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOllama(model=llm_config.MODEL_TAGGING, temperature=0.1)
            structured_llm = llm.with_structured_output(TagResponse)

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=content),
            ]

            response = await structured_llm.ainvoke(messages)
            if response and response.tags:
                return response.tags
            return []

        except Exception as e:
            logger.error("tagging_failed", error=str(e))
            return []
