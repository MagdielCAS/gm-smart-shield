"""
Page Summary Agent - Generates concise summaries for individual pages of RPG rulebooks.
"""

from typing import Optional
import structlog
from pydantic import BaseModel, Field

from gm_shield.shared.llm import config as llm_config

logger = structlog.get_logger(__name__)


class PageSummarySchema(BaseModel):
    """Structured output for page summary extraction."""
    summary: str = Field(
        description="A concise 1-3 sentence summary of the page's contents."
    )


class PageSummaryAgent:
    """
    Agent responsible for reading a single page of text and returning a brief summary
    to be used for RAG embedding and semantic search.
    """

    def __init__(self):
        self.system_prompt = """
        You are an AI assistant helping to categorize and index an RPG rulebook.
        Read the following text extracted from a single page of the rulebook.
        Write a concise, 1 to 3 sentence summary of what this page contains. 
        Focus on key terms, mechanics, or lore items presented (e.g., 'Combat rules and actions', 'List of level 1 Wizard spells', 'Character sheet template', 'Lore about the Elven city').
        If the page is mostly a chapter title, blank, or table of contents, explicitly state that.
        """

    async def summarize_page(self, text_content: str) -> Optional[str]:
        """
        Summarizes the provided text of a single page.

        Args:
            text_content: The text of the page.

        Returns:
            A concise summary string, or None if extraction fails.
        """
        if not text_content or not text_content.strip():
            return "Empty page."

        prompt = f"Summarize this rulebook page:\n\n{text_content}"

        try:
            logger.debug("page_summary_started")

            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage

            # Using the fast model for rapid page summarization
            llm = ChatOllama(model=llm_config.MODEL_FAST, temperature=0.0)
            structured_llm = llm.with_structured_output(PageSummarySchema)

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt),
            ]

            response = await structured_llm.ainvoke(messages)
            return response.summary if response else None

        except Exception as e:
            logger.error("page_summary_failed", error=str(e))
            return None
