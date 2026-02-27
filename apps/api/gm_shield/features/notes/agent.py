"""
Tagging Agent — Extracts keywords and tags from campaign notes.

Uses a local LLM to analyze note content and suggest relevant tags
for organization and linking.
"""

from typing import Any, List, Optional
from gm_shield.shared.ai.base import BaseAgent, AgentResponse, Citation
from gm_shield.shared.ai.ollama import OllamaAgent
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = get_logger(__name__)

TAGGING_AGENT_SYSTEM_PROMPT = """
You are the Tagging Agent for GM Smart Shield.
Your task is to analyze the provided campaign note and extract relevant tags and keywords.

OUTPUT FORMAT:
Return a JSON object with the following structure:
{{
  "tags": ["List", "of", "high-level", "categories"],
  "keywords": ["List", "of", "specific", "names", "or", "terms"],
  "summary": "One sentence summary of the note."
}}

GUIDELINES:
- Tags should be general categories like "NPC", "Location", "Quest", "Loot", "Lore".
- Keywords should be specific proper nouns (e.g., "Zarathon", "Ember Mountains").
- Ignore common words.

NOTE CONTENT:
{content}
"""


class TaggingAgent(BaseAgent):
    """
    Agent responsible for auto-tagging notes.
    """

    def __init__(self):
        self.ollama_agent = OllamaAgent(model_name=settings.OLLAMA_MODEL_GENERAL)
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", TAGGING_AGENT_SYSTEM_PROMPT), ("human", "Analyze this note.")]
        )
        self.chain = self.prompt | self.ollama_agent.llm | self.parser

    async def process(
        self,
        query: str, # Note content
        context: Optional[str] = None, # Not typically used for tagging, but kept for interface consistency
        citations: Optional[List[Citation]] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Generate tags for the note.
        """
        logger.info("tagging_agent_processing")

        try:
            # query here is the note content
            json_response = await self.chain.ainvoke({"content": query})

            import json
            text_response = json.dumps(json_response, indent=2)

            return AgentResponse(
                text=text_response,
                citations=[],
                metadata={"model": settings.OLLAMA_MODEL_GENERAL, "json_data": json_response},
            )
        except Exception as e:
            logger.error("tagging_agent_failed", error=str(e))
            return AgentResponse(
                text="Failed to tag note.",
                citations=[],
                metadata={"error": str(e)},
            )
