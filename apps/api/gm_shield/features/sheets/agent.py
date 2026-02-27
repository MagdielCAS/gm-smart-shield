"""
Sheet Agent — extracts character sheet templates from rulebooks.

Uses a local LLM to analyze rulebook text and generate a structured
Markdown character sheet template with frontmatter.
"""

from typing import Any, List, Optional, Dict
from gm_shield.shared.ai.base import BaseAgent, AgentResponse, Citation
from gm_shield.shared.ai.ollama import OllamaAgent
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = get_logger(__name__)

SHEET_AGENT_SYSTEM_PROMPT = """
You are the Sheet Agent for GM Smart Shield.
Your task is to analyze the provided text from a tabletop RPG rulebook and extract a character sheet template.

OUTPUT FORMAT:
Return a Markdown document that serves as a character sheet template.
- It MUST start with a YAML frontmatter block enclosed in `---`.
- The frontmatter should define fields for:
  - `name`: Character name
  - `player`: Player name
  - `class`: Character class/job (if applicable)
  - `race`: Character race/lineage (if applicable)
  - `level`: Character level (default 1)
  - Any other core stats defined in the text (e.g., Strength, Dexterity, etc.)
- The body of the Markdown should use headers and lists to organize the sheet (e.g., ## Attributes, ## Skills, ## Equipment).
- Do NOT fill in values for a specific character; leave them as placeholders (e.g., `[Value]`, `___`).
- Do NOT include conversational text before or after the Markdown.

CONTEXT:
{context}

SYSTEM NAME (Optional): {system_name}
"""


class SheetAgent(BaseAgent):
    """
    Agent responsible for generating character sheet templates.
    """

    def __init__(self):
        self.ollama_agent = OllamaAgent(model_name=settings.OLLAMA_MODEL_GENERAL)
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SHEET_AGENT_SYSTEM_PROMPT), ("human", "Generate a character sheet template based on the context.")]
        )
        self.chain = self.prompt | self.ollama_agent.llm | StrOutputParser()

    async def process(
        self,
        query: str, # In this case, query is just a trigger, context is what matters
        context: Optional[str] = None,
        citations: Optional[List[Citation]] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Generate a sheet template from the provided context.
        """
        system_name = kwargs.get("system_name", "Unknown System")
        logger.info("sheet_agent_processing", system=system_name)

        prompt_context = context if context else "No rulebook context provided."

        try:
            text_response = await self.chain.ainvoke(
                {"context": prompt_context, "system_name": system_name}
            )

            return AgentResponse(
                text=text_response,
                citations=citations or [],
                metadata={"model": settings.OLLAMA_MODEL_GENERAL},
            )
        except Exception as e:
            logger.error("sheet_agent_failed", error=str(e))
            return AgentResponse(
                text="Failed to generate character sheet template.",
                citations=[],
                metadata={"error": str(e)},
            )
