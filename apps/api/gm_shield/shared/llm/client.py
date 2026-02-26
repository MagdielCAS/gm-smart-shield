"""
Shared LLM Client (Ollama).

Provides a centralized AsyncClient for interacting with the local Ollama instance.
Handles connection pooling, logging, and common generation patterns.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from ollama import AsyncClient

from gm_shield.core.logging import get_logger
from gm_shield.shared.llm import config

logger = get_logger(__name__)


class OllamaClientWrapper:
    """
    Wrapper around ollama.AsyncClient providing structured logging and consistent error handling.
    """

    def __init__(self, host: str = config.OLLAMA_HOST):
        self.client = AsyncClient(host=host)
        self.host = host

    async def generate(
        self,
        prompt: str,
        model: str = config.MODEL_QUERY,
        system: Optional[str] = None,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a complete response (non-streaming).

        Args:
            prompt: The user prompt.
            model: The model name to use.
            system: Optional system prompt.
            format: Optional format (e.g. 'json').
            options: Optional generation parameters (temperature, etc.).

        Returns:
            The complete generated text.
        """
        logger.info("llm_generate_start", model=model)
        try:
            response = await self.client.generate(
                model=model,
                prompt=prompt,
                system=system,
                format=format,
                options=options,
                stream=False,
            )
            duration = response.get("total_duration")
            logger.info("llm_generate_complete", model=model, duration=duration)
            return response["response"]
        except Exception as e:
            logger.error("llm_generate_failed", model=model, error=str(e))
            raise

    async def stream(
        self,
        prompt: str,
        model: str = config.MODEL_QUERY,
        system: Optional[str] = None,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream the response chunk by chunk.

        Yields:
            Text chunks as they are generated.
        """
        logger.info("llm_stream_start", model=model)
        try:
            # According to Ollama python client docs, generate(stream=True) returns an async generator
            stream_gen = await self.client.generate(
                model=model,
                prompt=prompt,
                system=system,
                format=format,
                options=options,
                stream=True,
            )
            async for chunk in stream_gen:
                yield chunk["response"]

            logger.info("llm_stream_complete", model=model)
        except Exception as e:
            logger.error("llm_stream_failed", model=model, error=str(e))
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models on the Ollama server.

        Returns:
            A list of model dictionaries (name, size, digest, etc.).
        """
        try:
            response = await self.client.list()
            return response.get("models", [])
        except Exception as e:
            logger.error("llm_list_models_failed", error=str(e))
            raise


# Singleton instance
_client_instance = None


def get_llm_client() -> OllamaClientWrapper:
    """Return the shared Ollama client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OllamaClientWrapper()
    return _client_instance
