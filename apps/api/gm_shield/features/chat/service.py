"""
Chat feature — Service layer.

Orchestrates RAG: retrieves relevant knowledge from ChromaDB and
passes it as context to the Query Agent.
"""

from gm_shield.features.knowledge.service import query_knowledge
from gm_shield.features.chat.agent import QueryAgent
from gm_shield.shared.ai.base import AgentResponse, Citation
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """
    Handles the chat flow between user and Query Agent.
    """

    def __init__(self):
        self.agent = QueryAgent()

    async def get_response(self, query: str) -> AgentResponse:
        """
        Run the RAG pipeline: retrieval -> generation.
        """
        logger.info("chat_service_request", query=query)

        # 1. Retrieval
        try:
            chunks = await query_knowledge(query, top_k=5)

            # 2. Context & Citation preparation
            context_parts = []
            citations = []

            for chunk in chunks:
                content = chunk["content"]
                metadata = chunk["metadata"]
                source = metadata.get("source", "unknown")

                context_parts.append(f"Source: {source}\nContent: {content}")
                citations.append(
                    Citation(source=source, content=content, page=metadata.get("page"))
                )

            context = "\n\n---\n\n".join(context_parts)

            # 3. Generation
            response = await self.agent.process(
                query, context=context, citations=citations
            )
            return response

        except Exception as e:
            logger.error("chat_service_failed", error=str(e))
            return AgentResponse(
                text="I encountered an unexpected error while researching your question.",
                citations=[],
                metadata={"error": str(e)},
            )


# Singleton instance
_chat_service = ChatService()


def get_chat_service() -> ChatService:
    """Dependency provider for ChatService."""
    return _chat_service
