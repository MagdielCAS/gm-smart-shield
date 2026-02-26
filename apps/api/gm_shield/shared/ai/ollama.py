"""
Ollama integration for AI agents.

Wraps LangChain's Ollama support to provide a consistent interface for
local LLM inference across all agents.
"""

from typing import Any, List, Optional
from langchain_ollama import ChatOllama
from gm_shield.core.config import settings


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


class OllamaAgent:
    """
    Helper class for agents using Ollama models directly.
    Provides utility methods for prompt formatting and tool binding.
    """

    def __init__(self, model_name: str, system_prompt: Optional[str] = None):
        self.llm = get_llm(model_name)
        self.system_prompt = system_prompt

    def bind_tools(self, tools: List[Any]):
        """Bind tools to the underlying LLM for tool-calling capabilities."""
        self.llm = self.llm.bind_tools(tools)
