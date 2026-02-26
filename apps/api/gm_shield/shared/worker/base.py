"""
Abstract base class for background task queues — shared infrastructure.

Defines the common interface that all task queue backends must implement.
Current implementations:
- ``InMemoryTaskQueue`` (``shared.worker.memory``) — asyncio-based, suitable for development
- Redis / ARQ backend (planned for production)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Optional


class TaskQueue(ABC):
    """
    Abstract interface for a background task queue.

    Implementations can back this interface with an in-memory asyncio queue
    (for development) or a distributed queue such as ARQ / Celery (for production).

    All task queue backends (in-memory, Redis, etc.) must implement this interface
    so that feature slices can depend on the abstraction rather than a concrete backend.
    Swap implementations by changing the factory in ``shared.worker.memory``.
    """

    @abstractmethod
    async def enqueue(
        self,
        task: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Submit a coroutine (async task) for background execution.

        Args:
            task: An async callable (coroutine function) to execute.
            *args: Positional arguments forwarded to ``task``.
            **kwargs: Keyword arguments forwarded to ``task``.

        Returns:
            str: A unique task ID that can be used to query execution status.
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current status and result of an enqueued task.

        Args:
            task_id: The ID returned by :meth:`enqueue`.

        Returns:
            A dictionary containing at minimum a ``status`` key
            (``"pending"``, ``"running"``, ``"completed"``, or ``"failed"``),
            plus optional fields like ``result``, ``error``, ``enqueued_at``, ``started_at``, ``completed_at``.
            Returns ``None`` if the task ID is not recognised.
        """
        pass
