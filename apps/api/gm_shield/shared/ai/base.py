"""
Shared AI Agent infrastructure — abstract base classes and interfaces.

Defines the contract for all AI agents in the GM Smart Shield platform.
Standardizes how agents receive input, handle tool-calling, and format responses.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Reference to a specific knowledge source chunk."""

    source: str = Field(..., description="Filename or identifier of the source.")
    content: str = Field(..., description="The relevant text excerpt.")
    page: Optional[int] = Field(None, description="PDF page number if available.")


class AgentResponse(BaseModel):
    """Standardized response from an AI agent."""

    text: str = Field(..., description="The generated text response.")
    citations: List[Citation] = Field(
        default_factory=list, description="List of sources used."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional agent-specific metadata."
    )


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.

    Agents wrap LLM logic and provide a high-level `process` method.
    Subclasses must implement prompt engineering and logic specific to their role.
    """

    @abstractmethod
    async def process(
        self, query: str, context: Optional[str] = None, **kwargs: Any
    ) -> AgentResponse:
        """
        Execute the agent logic for a given query.

        Args:
            query: The user input or task description.
            context: Optional context data (e.g. retrieved from RAG).
            **kwargs: Agent-specific parameters.

        Returns:
            AgentResponse: Standardized result with text and citations.
        """
        pass
