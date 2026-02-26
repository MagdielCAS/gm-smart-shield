"""
Chat feature — service logic.

Handles the Query Agent logic:
1. Embeds user query using the shared embedding model.
2. Retrieves relevant chunks from ChromaDB (RAG).
3. Constructs a prompt with context.
4. Streams the response from Ollama.
"""

from typing import AsyncGenerator

from gm_shield.core.logging import get_logger
from gm_shield.features.knowledge.service import get_embedding_model
from gm_shield.shared.database.chroma import get_chroma_client
from gm_shield.shared.llm import config as llm_config
from gm_shield.shared.llm.agent import BaseAgent

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the GM's intelligent assistant. You answer questions based on the provided context from rulebooks and notes.
- If the answer is found in the context, be concise and accurate.
- If the answer is not in the context, say "I don't have that information in my knowledge base."
- Cite the source file (e.g. "PHB.pdf") if possible based on the context metadata.
"""


class QueryAgent(BaseAgent):
    """
    RAG-enabled Query Agent for answering GM questions.
    """

    def __init__(self):
        super().__init__(model=llm_config.MODEL_QUERY, system_prompt=SYSTEM_PROMPT)
        self.embedding_model = get_embedding_model()
        # We don't store the collection reference permanently to avoid staleness if re-initialized
        self.chroma_client = get_chroma_client()

    async def query(self, user_query: str) -> AsyncGenerator[str, None]:
        """
        Run the full RAG pipeline and stream the answer.

        Args:
            user_query: The question from the GM.

        Yields:
            Chunks of the answer text.
        """
        logger.info("rag_query_start", query=user_query)

        # 1. Embed query (CPU-bound, strictly speaking should be in executor if heavy,
        # but for single query it's fast enough)
        query_embedding = self.embedding_model.encode(user_query).tolist()

        # 2. Retrieve from ChromaDB
        try:
            collection = self.chroma_client.get_collection("knowledge_base")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,  # Retrieve top 3 chunks
                include=["documents", "metadatas"],
            )
            context_chunks = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
        except Exception as e:
            # Collection might not exist yet
            logger.warning("rag_retrieval_failed", error=str(e))
            context_chunks = []
            metadatas = []

        if not context_chunks:
            logger.info("rag_no_context_found")
            context_str = "No relevant context found in the knowledge base."
        else:
            context_str = "\n\n".join(
                [
                    f"[Source: {m.get('source', 'Unknown')}]\n{c}"
                    for c, m in zip(context_chunks, metadatas)
                ]
            )

        # 3. Build Prompt
        full_prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}\nAnswer:"

        logger.info("rag_retrieval_complete", chunk_count=len(context_chunks))

        # 4. Stream Response
        # We stream directly from the base agent
        async for chunk in self.stream(prompt=full_prompt):
            yield chunk
