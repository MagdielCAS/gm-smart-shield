"""
Sheet Agent - Extracts character sheet templates from rulebooks.
"""
from typing import Dict, Any, Optional
import structlog
from pydantic import BaseModel, Field

from gm_shield.shared.llm.client import OllamaClient, Message, Role

logger = structlog.get_logger(__name__)

class CharacterSheetSchema(BaseModel):
    """Structured output for character sheet extraction."""
    system_name: str = Field(description="The name of the RPG system (e.g., 'D&D 5e', 'Pathfinder 2e').")
    template_name: str = Field(description="A descriptive name for the template (e.g., 'Standard Character Sheet').")
    sections: Dict[str, Any] = Field(
        description="A dictionary representing the sections of the character sheet (e.g., Attributes, Skills, Equipment). Keys are section names, values are lists of fields or nested structures."
    )

class SheetAgent:
    """
    Agent responsible for analyzing rulebook text and extracting a structured
    character sheet template.
    """

    def __init__(self):
        self.client = OllamaClient()
        self.model = "llama3.2:3b" # Using the fast model for extraction

    async def extract_template(self, text_content: str) -> Optional[CharacterSheetSchema]:
        """
        Analyzes the provided text (rulebook content) and extracts a character sheet structure.

        Args:
            text_content: The full text or relevant subset of the rulebook.

        Returns:
            CharacterSheetSchema or None if extraction fails.
        """
        # Truncate text if too long to avoid context window issues,
        # specifically targeting sections that might describe character creation.
        # For a robust solution, we might want to RAG this first, but for now
        # we'll take a significant chunk.
        max_chars = 12000
        truncated_text = text_content[:max_chars]

        system_prompt = """
        You are an expert RPG system analyst. Your task is to extract the structure of a character sheet from the provided rulebook text.

        Identify the core components required to play a character in this system, such as:
        - Primary Attributes/Stats (e.g., Strength, Dexterity)
        - Derived Stats (e.g., HP, AC)
        - Skills or Proficiencies
        - Equipment slots
        - Biographical info (Name, Class, Level)

        Output the result as a JSON object matching the requested schema.
        Ensure the 'sections' field contains a logical grouping of these fields.
        """

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=f"Analyze this RPG text and extract the character sheet template:\n\n{truncated_text}")
        ]

        try:
            logger.info("sheet_agent_extraction_started", model=self.model)
            response = await self.client.generate(
                model=self.model,
                messages=messages,
                format=CharacterSheetSchema.model_json_schema(), # Force structured output
                stream=False
            )

            if not response.message or not response.message.content:
                logger.error("sheet_agent_empty_response")
                return None

            # Parse the JSON response
            import json
            data = json.loads(response.message.content)
            return CharacterSheetSchema(**data)

        except Exception as e:
            logger.error("sheet_agent_extraction_failed", error=str(e))
            return None
