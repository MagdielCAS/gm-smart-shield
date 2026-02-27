"""
Ollama integration for AI agents.

Wraps LangChain's Ollama support to provide a consistent interface for
local LLM inference across all agents.
"""

from typing import Any, List, Optional
from langchain_ollama import ChatOllama
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
import ollama

logger = get_logger(__name__)


def get_llm(model_name: str, temperature: float = 0.7) -> ChatOllama:
    """
    Initialise a LangChain ChatOllama instance for the configured local endpoint.

    Args:
        model_name: The name of the model to use (e.g. from settings).
        temperature: Controls randomness in the output.

    Returns:
        ChatOllama: A configured LangChain LLM instance.
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=model_name,
        temperature=temperature,
    )


def ensure_model_available(model_name: str) -> bool:
    """
    Checks if the model is available locally. If not, attempts to pull it.

    Args:
        model_name: The name of the model to check/pull.

    Returns:
        bool: True if model is available (or successfully pulled), False otherwise.
    """
    try:
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        models = client.list()

        # models['models'] is a list of objects with a 'model' key
        available_models = [m['model'] for m in models['models']]

        # Check for exact match or match without tag (e.g. llama3.2:3b matching llama3.2:3b)
        # Also handle cases where available model has :latest but request doesn't
        if any(m.startswith(model_name) for m in available_models):
            logger.info("model_already_available", model=model_name)
            return True

        logger.info("model_not_found_pulling", model=model_name)
        # Attempt to pull the model
        # stream=True allows us to potentially log progress, but for now we just wait
        client.pull(model_name)
        logger.info("model_pull_complete", model=model_name)
        return True

    except Exception as e:
        logger.error("ensure_model_available_failed", model=model_name, error=str(e))
        return False


class OllamaAgent:
    """
    Helper class for agents using Ollama models directly.
    Provides utility methods for prompt formatting and tool binding.
    """

    def __init__(self, model_name: str, system_prompt: Optional[str] = None):
        # Ensure model is available before initializing
        ensure_model_available(model_name)

        self.llm = get_llm(model_name)
        self.system_prompt = system_prompt

    def bind_tools(self, tools: List[Any]):
        """Bind tools to the underlying LLM for tool-calling capabilities."""
        self.llm = self.llm.bind_tools(tools)
