import asyncio
import uuid
from typing import Any, Callable, Coroutine, Dict, Optional
from datetime import datetime

from gm_shield.shared.worker.base import TaskQueue

class InMemoryTaskQueue(TaskQueue):
    """
    An in-memory task queue using asyncio.
    Suitable for local development and simple tasks, but not for heavy workloads or persistence across restarts.
    """

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        # In a real app, you might want to run tasks in a background thread or process
        # Here we just use asyncio.create_task

    async def enqueue(self, task: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "status": "pending",
            "enqueued_at": datetime.now(),
        }

        # Wrap the coroutine to handle exceptions and status updates
        async def worker():
            self.tasks[task_id]["status"] = "running"
            self.tasks[task_id]["started_at"] = datetime.now()
            try:
                result = await task(*args, **kwargs)
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["completed_at"] = datetime.now()
            except Exception as e:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
                self.tasks[task_id]["completed_at"] = datetime.now()

        # Fire and forget
        asyncio.create_task(worker())
        return task_id

    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)

# Singleton instance
memory_queue = InMemoryTaskQueue()

def get_task_queue() -> TaskQueue:
    return memory_queue
