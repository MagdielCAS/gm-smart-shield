"""
Encounter Agent — Generates creative encounters with NPC sheets.

Uses a local LLM (gemma3:12b-it-qat) to create detailed encounters
based on party level, environment, and theme.
"""

from typing import Any, List, Optional, Dict
from gm_shield.shared.ai.base import BaseAgent, AgentResponse, Citation
from gm_shield.shared.ai.ollama import OllamaAgent
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = get_logger(__name__)

ENCOUNTER_AGENT_SYSTEM_PROMPT = """
You are the Encounter Agent for GM Smart Shield.
Your task is to generate a creative, balanced encounter for a tabletop RPG based on the provided parameters.

PARAMETERS:
- Party Level: {level}
- Environment: {environment}
- Difficulty: {difficulty}
- Theme: {theme}

OUTPUT FORMAT:
Return a JSON object with the following structure:
{{
  "title": "A creative title",
  "description": "Narrative description for the GM to read or paraphrase.",
  "tactics": "How the enemies behave in combat.",
  "npc_stats": [
    {{ "name": "Enemy Name", "cr": "Challenge Rating", "hp": "Health", "ac": "Armor Class", "attacks": "Brief list of attacks" }}
  ],
  "loot": "Suggested rewards or treasure."
}}

CONTEXT (Optional Rules/Lore):
{context}

Ensure the encounter is appropriate for the party level and difficulty.
"""

class EncounterAgent(BaseAgent):
    """
    Agent responsible for generating creative encounters.
    """

    def __init__(self):
        # Ensure model is available, using the creative model configuration
        self.ollama_agent = OllamaAgent(model_name=settings.OLLAMA_MODEL_CREATIVE)

        # Using JsonOutputParser to enforce structured output
        self.parser = JsonOutputParser()

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", ENCOUNTER_AGENT_SYSTEM_PROMPT), ("human", "Generate an encounter.")]
        )
        self.chain = self.prompt | self.ollama_agent.llm | self.parser

    async def process(
        self,
        query: str,
        context: Optional[str] = None,
        citations: Optional[List[Citation]] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Generate an encounter.
        """
        level = kwargs.get("level", 1)
        environment = kwargs.get("environment", "Unknown")
        difficulty = kwargs.get("difficulty", "Medium")
        theme = kwargs.get("theme", "None")

        logger.info("encounter_agent_processing", level=level, environment=environment)

        prompt_context = context if context else "No specific context provided."

        try:
            json_response = await self.chain.ainvoke(
                {
                    "context": prompt_context,
                    "level": level,
                    "environment": environment,
                    "difficulty": difficulty,
                    "theme": theme
                }
            )

            # Since AgentResponse expects text, we'll serialize the JSON back to a string for the 'text' field
            # But we can also pass the raw dict in metadata for the service layer to use
            import json
            text_response = json.dumps(json_response, indent=2)

            return AgentResponse(
                text=text_response,
                citations=citations or [],
                metadata={"model": settings.OLLAMA_MODEL_CREATIVE, "json_data": json_response},
            )
        except Exception as e:
            logger.error("encounter_agent_failed", error=str(e))
            return AgentResponse(
                text="Failed to generate encounter.",
                citations=[],
                metadata={"error": str(e)},
            )
