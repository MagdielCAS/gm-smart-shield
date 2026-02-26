"""
Query Agent — handles general Q&A against the knowledge base.

Uses a local LLM (llama3.2:3b by default) to answer questions based on
retrieved knowledge context.
"""

from typing import Any, List, Optional
from gm_shield.shared.ai.base import BaseAgent, AgentResponse, Citation
from gm_shield.shared.ai.ollama import OllamaAgent
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = get_logger(__name__)

QUERY_AGENT_SYSTEM_PROMPT = """
You are the Query Agent for GM Smart Shield, an AI assistant for Tabletop RPG Game Masters.
Your goal is to provide accurate, concise, and helpful answers based ONLY on the provided context.

GUIDELINES:
1. If the context contains the answer, provide it clearly.
2. If the context does not contain the answer, say "I don't have enough information in the knowledge base to answer that."
3. cite your sources by referencing the source filename or ID provided in the context.
4. Keep the tone helpful and GM-focused.
5. Use Markdown for formatting (bolding, lists, etc.).

Context:
{context}
"""


class QueryAgent(BaseAgent):
    """
    Agent responsible for answering questions using RAG.
    """

    def __init__(self):
        self.ollama_agent = OllamaAgent(model_name=settings.OLLAMA_MODEL_GENERAL)
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", QUERY_AGENT_SYSTEM_PROMPT), ("human", "{query}")]
        )
        self.chain = self.prompt | self.ollama_agent.llm | StrOutputParser()

    async def process(
        self,
        query: str,
        context: Optional[str] = None,
        citations: Optional[List[Citation]] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Produce an answer based on the provided context using an LCEL chain.
        """
        logger.info("query_agent_processing", query=query)

        prompt_context = context if context else "No context provided."

        try:
            text_response = await self.chain.ainvoke(
                {"context": prompt_context, "query": query}
            )

            return AgentResponse(
                text=text_response,
                citations=citations or [],
                metadata={"model": settings.OLLAMA_MODEL_GENERAL},
            )
        except Exception as e:
            logger.error("query_agent_failed", error=str(e))
            return AgentResponse(
                text="I encountered an error while trying to process your request.",
                citations=[],
                metadata={"error": str(e)},
            )
