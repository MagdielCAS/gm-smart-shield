"""
Reference Agent - Extracts quick reference items (spells, items) from rulebooks.
"""

from typing import List
import structlog
from pydantic import BaseModel, Field

from gm_shield.shared.llm import config as llm_config

logger = structlog.get_logger(__name__)


class ReferenceItem(BaseModel):
    """A single reference item (spell, item, feat, etc)."""

    name: str = Field(description="The name of the item/spell.")
    category: str = Field(
        description="The category (e.g., Spell, Weapon, Feat, Monster)."
    )
    description: str = Field(
        description="A concise summary of the effect or properties."
    )
    tags: List[str] = Field(
        description="Keywords or tags (e.g., 'Evocation', 'Finesse')."
    )


class ReferenceList(BaseModel):
    """List of reference items."""

    items: List[ReferenceItem]


class ReferenceAgent:
    """
    Agent responsible for extracting lists of reference items from text.
    """

    def __init__(self):
        self.model_name = llm_config.MODEL_REFERENCE_SMART

    async def extract_references(
        self, text_chunk: str, category_hint: str = "items or spells"
    ) -> List[ReferenceItem]:
        """
        Analyzes a chunk of text and extracts structured reference items.
        """
        system_prompt = f"""
        You are an RPG data extractor. Your job is to read the provided text and identify any {category_hint}.

        For each item found, extract:
        - Name
        - Category (be specific, e.g., 'Level 1 Spell', 'Martial Weapon')
        - Description (summarize the mechanical effect)
        - Tags (keywords)

        Return a JSON list of objects. If no items are found, return an empty list.
        """

        prompt = f"Extract {category_hint} from this text:\n\n{text_chunk}"

        try:
            logger.info("reference_extraction_started", model=self.model_name)

            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOllama(model=self.model_name, temperature=0.1)
            structured_llm = llm.with_structured_output(ReferenceList)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt),
            ]

            response = await structured_llm.ainvoke(messages)
            if response and response.items:
                return response.items
            return []

        except Exception as e:
            logger.error("reference_extraction_failed", error=str(e))
            return []
