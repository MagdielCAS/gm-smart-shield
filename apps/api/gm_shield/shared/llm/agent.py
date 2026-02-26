"""
Base Agent.

Provides a foundational class for all specific agents, handling prompt construction,
LLM interaction, and logging.
"""

from typing import AsyncGenerator

from gm_shield.core.logging import get_logger
from gm_shield.shared.llm.client import get_llm_client

logger = get_logger(__name__)


class BaseAgent:
    """
    Abstract base class for AI Agents.

    Encapsulates the model selection and system prompt, providing consistent
    interface for generation and streaming.
    """

    def __init__(self, model: str, system_prompt: str):
        """
        Initialize the agent.

        Args:
            model: The name of the Ollama model to use.
            system_prompt: The system prompt defining the agent's persona and constraints.
        """
        self.model = model
        self.system_prompt = system_prompt
        self.client = get_llm_client()

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a complete response for the given prompt.

        Args:
            prompt: The user input.
            **kwargs: Additional options passed to the LLM (e.g., format, options).

        Returns:
            The generated text response.
        """
        logger.info(
            "agent_generate_start", agent=self.__class__.__name__, model=self.model
        )
        try:
            return await self.client.generate(
                prompt=prompt, model=self.model, system=self.system_prompt, **kwargs
            )
        except Exception as e:
            logger.error(
                "agent_generate_failed", agent=self.__class__.__name__, error=str(e)
            )
            raise

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream the response for the given prompt.

        Args:
            prompt: The user input.
            **kwargs: Additional options passed to the LLM.

        Yields:
            Text chunks as they are generated.
        """
        logger.info(
            "agent_stream_start", agent=self.__class__.__name__, model=self.model
        )
        try:
            async for chunk in self.client.stream(
                prompt=prompt, model=self.model, system=self.system_prompt, **kwargs
            ):
                yield chunk
        except Exception as e:
            logger.error(
                "agent_stream_failed", agent=self.__class__.__name__, error=str(e)
            )
            raise
x