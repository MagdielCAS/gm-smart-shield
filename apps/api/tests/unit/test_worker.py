import pytest
import asyncio
from gm_shield.shared.worker.memory import InMemoryTaskQueue


@pytest.mark.asyncio
async def test_worker_enqueue():
    queue = InMemoryTaskQueue()

    async def sample_task(x, y):
        return x + y

    task_id = await queue.enqueue(sample_task, 3, 4)
    assert task_id is not None

    # Wait for task to complete
    for _ in range(10):
        status = await queue.get_status(task_id)
        if status["status"] == "completed":
            break
        await asyncio.sleep(0.1)

    assert status["status"] == "completed"
    assert status["result"] == 7


@pytest.mark.asyncio
async def test_worker_get_status_non_existent():
    queue = InMemoryTaskQueue()
    # Call get_status with a random UUID
    status = await queue.get_status("non-existent-id")
    assert status is None
