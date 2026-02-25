from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Optional


class TaskQueue(ABC):
    """
    Abstract base class for a task queue.
    """

    @abstractmethod
    async def enqueue(
        self, task: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ) -> str:
        """
        Enqueue a task.
        :param task: The async function to execute.
        :param args: Positional arguments for the task.
        :param kwargs: Keyword arguments for the task.
        :return: A task ID.
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        :param task_id: The ID of the task.
        :return: A dictionary with task status and result, or None if not found.
        """
        pass
