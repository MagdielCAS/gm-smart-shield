"""
Chat feature — API models.
"""

from pydantic import BaseModel, Field
from gm_shield.shared.ai.base import AgentResponse


class ChatRequest(BaseModel):
    """Payload for a chat query."""

    query: str = Field(..., description="The user's question or instruction.")


class ChatResponse(AgentResponse):
    """Standardized chat response (inherited from AgentResponse)."""

    pass
