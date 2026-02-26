"""
Chat feature — data models.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request payload for the Query Agent.
    """

    query: str = Field(
        ...,
        description="The user's question or command.",
        min_length=1,
        examples=["What is a short rest?"],
    )
