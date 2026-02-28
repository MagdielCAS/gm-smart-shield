"""
Shared LLM Client for Ollama.
"""

import json
import httpx
from typing import List, Optional, Any, AsyncGenerator, Dict, Union
from enum import Enum
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    images: Optional[List[str]] = None


class ChatResponse(BaseModel):
    model: str
    created_at: str
    message: Optional[Message] = None
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaClient:
    """
    Async client for Ollama API.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def generate(
        self,
        model: str,
        messages: List[Message],
        stream: bool = False,
        format: Optional[Union[str, Dict[str, Any]]] = None,  # JSON schema or 'json'
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponse, None]]:
        """
        Generate a chat completion.
        """
        payload = {
            "model": model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "stream": stream,
        }

        if format:
            payload["format"] = format

        if options:
            payload["options"] = options

        try:
            if stream:
                return self._stream_response(payload)
            else:
                response = await self.client.post("/api/chat", json=payload)
                response.raise_for_status()
                return ChatResponse(**response.json())

        except httpx.RequestError as e:
            logger.error("ollama_request_failed", error=str(e))
            raise

    async def _stream_response(
        self, payload: Dict[str, Any]
    ) -> AsyncGenerator[ChatResponse, None]:
        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield ChatResponse(**data)
                except json.JSONDecodeError:
                    logger.warning("ollama_stream_decode_error", line=line)
                    continue

    async def list_models(self) -> List[str]:
        """List available local models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error("ollama_list_models_failed", error=str(e))
            return []

    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Pull a model from the library."""
        payload = {"name": model}
        async with self.client.stream("POST", "/api/pull", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                yield json.loads(line)


_client_instance = None


def get_llm_client() -> OllamaClient:
    """Returns a singleton instance of the Ollama client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OllamaClient()
    return _client_instance
