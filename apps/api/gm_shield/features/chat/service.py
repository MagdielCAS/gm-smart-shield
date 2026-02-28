"""
Chat feature — service logic.

Handles the Query Agent logic:
1. Embeds user query using the shared embedding model.
2. Retrieves relevant chunks from ChromaDB (RAG).
3. Constructs a prompt with context.
4. Streams the response from Ollama.
"""

import sys
from typing import AsyncGenerator
from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import AsyncCallbackHandler

from gm_shield.core.logging import get_logger
from gm_shield.shared.llm import config as llm_config
from gm_shield.shared.llm.subagents import SUBAGENTS
from langchain_mcp_adapters.tools import load_mcp_tools

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the GM's intelligent assistant and orchestrator.
Use the provided tools and delegated subagents to answer questions or perform tasks (like generating encounters, creating notes, or querying the knowledge base).
- If you need to generate an encounter, use the encounter generator.
- If you need to search rules or lore, use the knowledge base tool.
- Always provide concise, helpful answers.
"""


class QueryAgent:
    """
    Main Orchestrator Agent. Uses deepagents and LangChain to route queries to tools and subagents.
    """

    def __init__(self):
        self.model = llm_config.MODEL_QUERY

    async def _get_mcp_tools(self):
        """Fetch tools from the local MCP server via stdio."""
        from mcp import StdioServerParameters

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gm_shield.features.mcp.server_stdio"],
        )
        # In a real long-running scenario we'd keep the session alive.
        # For this execution, we'll initialize, get tools, and return them.
        # However, Langchain MCP adapters handle the lifecycle.
        return load_mcp_tools([server_params])

    async def query(self, user_query: str) -> AsyncGenerator[str, None]:
        """
        Run the agent orchestrator and stream the answer.
        """
        logger.info("orchestrator_query_start", query=user_query)

        class AsyncIteratorCallbackHandler(AsyncCallbackHandler):
            def __init__(self):
                import asyncio

                self.queue = asyncio.Queue()
                self.done = False

            async def on_chat_model_start(self, *args, **kwargs):
                pass

            async def on_llm_new_token(self, token: str, **kwargs) -> None:
                if token is not None:
                    self.queue.put_nowait(token)

            async def on_llm_end(self, *args, **kwargs) -> None:
                self.done = True
                self.queue.put_nowait(None)

            async def on_llm_error(self, *args, **kwargs) -> None:
                self.done = True
                self.queue.put_nowait(None)

        try:
            # We need to use langchain_mcp_adapters to load tools
            # Let's import it inline.
            from langchain_mcp_adapters.tools import load_mcp_tools
            from mcp import StdioServerParameters
            import sys

            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "gm_shield.features.mcp.server_stdio"],
            )

            # Using async with context manager for tools
            async with load_mcp_tools([server_params]) as mcp_tools:
                agent = create_deep_agent(
                    name="QueryOrchestrator",
                    model=f"ollama:{self.model}",
                    subagents=SUBAGENTS,
                    tools=mcp_tools,
                    system_prompt=SYSTEM_PROMPT,
                    # deepagents allows callbacks via run_config but we can also just stream
                )

                # deepagents compiled graphs stream events natively
                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=user_query)]}, version="v1"
                ):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            yield chunk.content

        except Exception as e:
            logger.error("orchestrator_query_failed", error=str(e))
            yield "I'm sorry, an error occurred while processing your request."
