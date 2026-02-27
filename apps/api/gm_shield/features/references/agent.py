"""
Reference Agent — generates quick references from rulebooks.

Uses a local LLM to extract and summarize rules for specific categories
(e.g., Spells, Conditions) into a concise Markdown format.
"""

from typing import Any, List, Optional
from gm_shield.shared.ai.base import BaseAgent, AgentResponse, Citation
from gm_shield.shared.ai.ollama import OllamaAgent
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = get_logger(__name__)

REFERENCE_AGENT_SYSTEM_PROMPT = """
You are the Reference Agent for GM Smart Shield.
Your task is to generate a concise, structured quick reference guide for a specific category based on the provided rulebook text.

CATEGORY: {category}

OUTPUT FORMAT:
Return a Markdown document.
- Use clear headers for each item (e.g., if category is "Spells", each spell gets a header).
- For each item, provide a summary of the key rules, mechanics, or stats.
- Keep it concise—this is for quick reference at the game table.
- Do NOT include conversational filler.

CONTEXT:
{context}
"""


class ReferenceAgent(BaseAgent):
    """
    Agent responsible for generating quick reference cards.
    """

    def __init__(self):
        self.ollama_agent = OllamaAgent(model_name=settings.OLLAMA_MODEL_GENERAL)
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", REFERENCE_AGENT_SYSTEM_PROMPT), ("human", "Generate a quick reference for {category} based on the context.")]
        )
        self.chain = self.prompt | self.ollama_agent.llm | StrOutputParser()

    async def process(
        self,
        query: str, # Trigger
        context: Optional[str] = None,
        citations: Optional[List[Citation]] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Generate reference content.
        """
        category = kwargs.get("category", "General")
        logger.info("reference_agent_processing", category=category)

        prompt_context = context if context else "No context provided."

        try:
            text_response = await self.chain.ainvoke(
                {"context": prompt_context, "category": category}
            )

            return AgentResponse(
                text=text_response,
                citations=citations or [],
                metadata={"model": settings.OLLAMA_MODEL_GENERAL},
            )
        except Exception as e:
            logger.error("reference_agent_failed", error=str(e))
            return AgentResponse(
                text=f"Failed to generate references for {category}.",
                citations=[],
                metadata={"error": str(e)},
            )
