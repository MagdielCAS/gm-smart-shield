---
description: Python API coding and documentation rules for apps/api
globs:
  - apps/api/**
---

# API Rules — `apps/api/`

## Code organisation

- Package root: `apps/api/gm_shield/`.
- Use **vertical slices** under `features/<slice>/`:
  - `routes.py` — HTTP router only (thin).
  - `service.py` — business logic.
  - `models.py` — Pydantic schemas.
- `shared/` for cross-slice utilities; `core/` for global config and app bootstrap.
- Register new routers in `gm_shield/main.py`.

---

## Documentation patterns

### Module docstring (required on every `.py` file)

```python
"""
Knowledge feature — ingestion service.

Handles all CPU-bound document processing: text extraction, chunking,
local embedding generation, and ChromaDB storage.

Supported file formats: PDF (.pdf), plain text (.txt), Markdown (.md), CSV (.csv).
"""
```

### Function docstrings — Google style

Use `Args:`, `Returns:`, `Raises:`. Cross-reference with `:func:\`module.name\``.

```python
def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a file, dispatching to the appropriate parser.

    Args:
        file_path: Absolute or relative path to the source file.
            Supported extensions: ``.pdf``, ``.txt``, ``.md``, ``.csv``.

    Returns:
        The full extracted text as a single string.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist on disk.
        ValueError: If the file extension is not supported.
    """
```

### Section banners

Group related code with em-dash banners (79-char width):

```python
# ── Text extraction ──────────────────────────────────────────────────────────
```

### Pipeline step comments

Number steps inside multi-stage pipelines:

```python
    # Step 1 — Extract
    text = extract_text_from_file(file_path)

    # Step 2 — Chunk
    chunks = text_splitter.split_text(text)

    # Step 3 — Embed
    embeddings = model.encode(chunks)

    # Step 4 — Store in ChromaDB
    collection.add(...)
```

### FastAPI endpoint decorator (Swagger metadata required)

Every route must have `summary`, `description` (Markdown), and `responses`:

```python
@router.post(
    "/",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a knowledge source document",
    description=(
        "Accepts a file path and enqueues an asynchronous ingestion job.\n\n"
        "**Processing pipeline (runs in background):**\n"
        "1. Extract text  2. Chunk  3. Embed  4. Store in ChromaDB\n\n"
        "Poll `GET /api/v1/tasks/{task_id}` to track progress."
    ),
    responses={
        status.HTTP_202_ACCEPTED: {"description": "Task enqueued."},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Validation error."},
    },
)
async def add_knowledge_source(source: KnowledgeSourceCreate):
    """Full prose docstring for editors/linters."""
```

### Pydantic models

Every class gets a docstring. Every `Field` needs `description=` and `examples=[...]`:

```python
class KnowledgeSourceCreate(BaseModel):
    """Payload for ingesting a new knowledge source document."""

    file_path: str = Field(
        ...,
        description="Absolute or relative path to the source file.",
        examples=["/data/uploads/monster-manual.pdf"],
    )
```

---

## Testing rules

| Test type | Location |
|---|---|
| Pure-function unit | `tests/unit/test_<module>.py` |
| HTTP / integration | `tests/unit/test_<feature>.py` (TestClient) |
| BDD / Gherkin | `tests/features/<name>.feature` + `tests/features/steps/` |

All tests must be **deterministic** — no real network, no real DB (use `tmp_path` or mocks).

### Unit test example

```python
# tests/unit/test_knowledge_extraction.py
def test_extract_text_unsupported(tmp_path):
    bad_file = tmp_path / "test.exe"
    bad_file.touch()
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text_from_file(str(bad_file))

def test_extract_text_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("non_existent_file.txt")
```

### HTTP test example (TestClient + fixture override)

```python
# tests/unit/test_knowledge_service.py
@pytest.fixture
def mock_queue():
    with patch("gm_shield.features.knowledge.router.get_task_queue") as mock:
        queue = AsyncMock()
        mock.return_value = queue
        queue.enqueue.return_value = "mock_task_id"
        yield queue

def test_add_knowledge_source(mock_queue):
    response = client.post("/api/v1/knowledge/", json={"file_path": "/data/test.pdf"})
    assert response.status_code == 202
    assert response.json()["task_id"] == "mock_task_id"
```

### Async test example

```python
@patch("gm_shield.features.knowledge.service.get_embedding_model")
@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_process_knowledge_source(mock_chroma, mock_embed):
    ...
    result = await process_knowledge_source("/path/to/test.txt")
    assert "Processed" in result
```

### BDD / Gherkin example

```gherkin
# tests/features/knowledge_ingestion.feature
Feature: Knowledge ingestion

  Scenario: Successful document ingestion
    Given the API is running
    When I POST to "/api/v1/knowledge/" with a valid PDF path
    Then the response status code should be 202
    And the response body should contain a "task_id"
```

```python
# tests/features/steps/knowledge_ingestion_steps.py
from pytest_bdd import given, when, then, parsers

@when("I POST to \"/api/v1/knowledge/\" with a valid PDF path", target_fixture="response")
def post_knowledge(api_client):
    return api_client.post("/api/v1/knowledge/", json={"file_path": "/data/test.pdf"})

@then(parsers.parse("the response status code should be {code:d}"))
def check_status(response, code):
    assert response.status_code == code
```

### Fixtures

Use shared fixtures from `tests/conftest.py`:
- `db_session` — in-memory SQLite, rolled back after each test.
- `client` — `TestClient` with `get_db` overridden to `db_session`.

---

## Test commands

```bash
cd apps/api && uv run python -m pytest           # all tests
cd apps/api && uv run python -m pytest tests/unit -q
cd apps/api && uv run python -m pytest tests/features -q
cd apps/api && uv run python -m pytest -k "knowledge" -q
```
