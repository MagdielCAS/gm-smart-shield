from fastapi import APIRouter
from gm_shield.features.knowledge.models import KnowledgeSourceCreate, KnowledgeSourceResponse
from gm_shield.features.knowledge.service import process_knowledge_source
from gm_shield.shared.worker.memory import get_task_queue

router = APIRouter()

@router.post("/", response_model=KnowledgeSourceResponse)
async def add_knowledge_source(source: KnowledgeSourceCreate):
    """
    Add a new knowledge source (file) to be processed.
    """
    queue = get_task_queue()

    # Enqueue the background task
    # We pass the function reference and arguments
    task_id = await queue.enqueue(process_knowledge_source, source.file_path)

    return KnowledgeSourceResponse(
        task_id=task_id,
        status="pending",
        message=f"Processing started for {source.file_path}"
    )
