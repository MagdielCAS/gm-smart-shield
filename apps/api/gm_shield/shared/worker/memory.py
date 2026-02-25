"""
In-memory task queue implementation — shared infrastructure.

Uses ``asyncio.create_task`` to run background coroutines within the same
event loop as the FastAPI application. Task state (status, result, timestamps)
is stored in a plain dict and is **not** persisted across application restarts.

This backend is designed for local development and lightweight workloads.
For production use, replace with a Redis-backed queue (e.g. ARQ).

Usage::

    from gm_shield.shared.worker.memory import get_task_queue

    queue = get_task_queue()
    task_id = await queue.enqueue(my_async_function, arg1, arg2)
    status = await queue.get_status(task_id)
"""

import asyncio
import uuid
from typing import Any, Callable, Coroutine, Dict, Optional
from datetime import datetime

from gm_shield.shared.worker.base import TaskQueue


class InMemoryTaskQueue(TaskQueue):
    """
    Asyncio-based in-memory background task queue.

    Wraps submitted tasks in a lifecycle-tracking coroutine that updates the
    task dict through the following status transitions::

        pending → running → completed
                          ↘ failed

    Timestamps (``enqueued_at``, ``started_at``, ``completed_at``) are recorded
    at each transition for basic observability.

    **Limitations:**
    - State is lost on process restart — tasks are not persisted.
    - Not suitable for CPU-bound work that blocks the event loop for > a few ms
      (use ``asyncio.get_event_loop().run_in_executor`` inside the task itself).
    - No retry logic — failed tasks must be re-submitted manually.
    """

    def __init__(self) -> None:
        # Maps task_id → task state dict.
        self.tasks: Dict[str, Dict[str, Any]] = {}
        # Keeps strong references to running Task objects so they are not
        # garbage-collected before they complete (asyncio requirement).
        self._background_tasks: set[asyncio.Task] = set()

    async def enqueue(
        self,
        task: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Schedule an async task for immediate background execution.

        Creates a ``asyncio.Task`` (fire-and-forget) and stores the task ID in
        the internal registry with an initial ``"pending"`` status.

        Args:
            task: An async callable to execute in the background.
            *args: Positional arguments forwarded to ``task``.
            **kwargs: Keyword arguments forwarded to ``task``.

        Returns:
            str: A UUID-based task ID for status polling.
        """
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "status": "pending",
            "enqueued_at": datetime.now(),
        }

        async def _worker() -> None:
            """Lifecycle wrapper that tracks status transitions and captures errors."""
            self.tasks[task_id]["status"] = "running"
            self.tasks[task_id]["started_at"] = datetime.now()
            try:
                result = await task(*args, **kwargs)
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["result"] = result
            except Exception as e:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
            finally:
                self.tasks[task_id]["completed_at"] = datetime.now()

        # Fire and forget — discarded from the set once the Task finishes.
        t = asyncio.create_task(_worker())
        self._background_tasks.add(t)
        t.add_done_callback(self._background_tasks.discard)

        return task_id

    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Return the current state of an enqueued task.

        Args:
            task_id: A task ID previously returned by ``enqueue``.

        Returns:
            A dict with at minimum ``{"status": str, "enqueued_at": datetime}``.
            Additional fields appear depending on the task lifecycle stage:

            - ``running`` adds ``started_at``
            - ``completed`` adds ``result`` and ``completed_at``
            - ``failed`` adds ``error`` and ``completed_at``

            Returns ``None`` if the task ID is not found.
        """
        return self.tasks.get(task_id)


# ── Singleton ─────────────────────────────────────────────────────────────────
# Shared across all requests in the process — avoids re-creating queue state
# on every dependency injection call.
_memory_queue = InMemoryTaskQueue()


def get_task_queue() -> TaskQueue:
    """
    Return the singleton in-memory task queue instance.

    Intended for use as a plain function call (not a FastAPI ``Depends``),
    since the queue is a process-level singleton rather than a request-scoped object.

    Returns:
        TaskQueue: The active task queue backend.
    """
    return _memory_queue
