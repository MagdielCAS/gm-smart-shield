# AGENTS.md (apps/api)

## Scope

These rules apply to all files under `apps/api/`.

---

## Code organisation rules

- Package root: `apps/api/gm_shield/`.
- Keep **vertical-slice boundaries**:
  - `features/<slice>/` contains `routes.py`, `service.py`, and `models.py` for that feature.
  - `shared/` holds reusable cross-slice components (DB adapters, worker abstractions).
  - `core/` holds global configuration and app-level wiring.
- Avoid circular imports; depend inward on `shared/` and `core/` primitives.
- Keep endpoint modules thin; move non-trivial logic into the slice-level `service.py`.
- Place new routers in their slice folder and register them from `gm_shield/main.py`.

---

## Documentation & comment patterns

All code **must** follow the conventions below. They are enforced because they feed the Swagger
UI docs automatically and keep the codebase navigable.

### 1 — Module-level docstring

Every `.py` file starts with a triple-quoted docstring describing the module's role:

```python
"""
Knowledge feature — ingestion service.

Handles all CPU-bound document processing: text extraction, chunking,
local embedding generation, and ChromaDB storage. Because these operations
are I/O- and CPU-heavy, the main entry point (`process_knowledge_source`)
offloads the work to a thread-pool executor so the AsyncIO event loop is
never blocked.

Supported file formats: PDF (.pdf), plain text (.txt), Markdown (.md), CSV (.csv).
"""
```

### 2 — Function / method docstrings (Google style)

Use **Google-style docstrings** with `Args:`, `Returns:`, and `Raises:` sections. Write
`Args:` sub-items as `name: description` on one indented line; wrap prose below if needed.
Format cross-references as `:func:\`module.name\`` (Sphinx-compatible):

```python
def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a file, dispatching to the appropriate parser by extension.

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

- Short one-liner functions may use a single-line docstring: `"""API root — redirects clients to the interactive docs."""`
- Private helpers (`_prefixed`) still get docstrings, with an explicit note if they are
  blocking / intended for thread-pool use:

```python
def _process_sync(file_path: str) -> str:
    """
    Run the full ingestion pipeline for a single file (blocking).

    Intended to be called inside a thread-pool executor via
    :func:`process_knowledge_source` so the event loop is not blocked.
    """
```

### 3 — Section banners

Group logically related code blocks with an ASCII banner using the em-dash style. Keep the
total line width at 79 characters:

```python
# ── Embedding model ──────────────────────────────────────────────────────────
# Using a lightweight local model that runs entirely offline.
# Loaded once and reused across all ingestion jobs (lazy singleton pattern).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ── Text extraction ──────────────────────────────────────────────────────────

# ── Core processing pipeline ─────────────────────────────────────────────────

# ── Async entry point ────────────────────────────────────────────────────────
```

In `main.py`, use banners to separate router registration blocks:

```python
# ── Feature routers ─────────────────────────────────────────────────────────
# Each router is registered with a prefix that matches the API design in TECHNICAL.md.
```

### 4 — Inline step comments inside pipelines

When a function executes a numbered pipeline (extract → chunk → embed → store), annotate
each phase with `# Step N — <Label>`:

```python
    # Step 1 — Extract
    text = extract_text_from_file(file_path)

    # Step 2 — Chunk
    # RecursiveCharacterTextSplitter tries to keep paragraphs/sentences intact.
    chunks = text_splitter.split_text(text)

    # Step 3 — Embed
    embeddings = model.encode(chunks)

    # Step 4 — Store in ChromaDB
    # IDs are randomised per ingestion run to allow re-processing the same file.
    collection.add(...)
```

### 5 — FastAPI endpoint decorators (Swagger metadata)

Every `@router.*` decorator must include `summary`, `description`, and `responses`.
Use a multiline string for the description and apply Markdown to highlight key info:

```python
@router.post(
    "/",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a knowledge source document",
    description=(
        "Accepts a file path and enqueues an asynchronous ingestion job.\n\n"
        "**Processing pipeline (runs in background):**\n"
        "1. Extract text from the file (PDF / Markdown / TXT / CSV)\n"
        "2. Split text into overlapping chunks (~1 000 tokens each)\n"
        "3. Embed chunks with `all-MiniLM-L6-v2` (sentence-transformers)\n"
        "4. Store embeddings in ChromaDB under the `knowledge_base` collection\n\n"
        "Poll `GET /api/v1/tasks/{task_id}` to track processing progress."
    ),
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Ingestion task accepted and enqueued successfully."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Validation error — file_path is missing or malformed."
        },
    },
)
async def add_knowledge_source(source: KnowledgeSourceCreate):
    """
    Full prose docstring here — Swagger uses the decorator description,
    but this docstring is used by editors and linters.
    """
```

Keep the function docstring in sync with the decorator description; they serve different
audiences (developer tools vs. Swagger UI).

### 6 — Pydantic models (`models.py`)

- Add a class-level docstring explaining the model's purpose and any constraints.
- Every `Field` must include `description=` and at least one `examples=[...]` value.

```python
class KnowledgeSourceCreate(BaseModel):
    """
    Payload for ingesting a new knowledge source document.

    The file must already exist on the local filesystem at the given path.
    Supported formats: `.pdf`, `.md`, `.txt`, `.csv`.
    """

    file_path: str = Field(
        ...,
        description=(
            "Absolute or relative path to the source file on the local filesystem. "
            "Supported formats: PDF (.pdf), Markdown (.md), plain text (.txt), CSV (.csv)."
        ),
        examples=["/data/uploads/monster-manual.pdf"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional human-readable label for this knowledge source.",
        examples=["D&D 5e Monster Manual"],
    )
```

### 7 — `main.py` application metadata

- Set `_DESCRIPTION` as a module-level constant (Markdown string) and pass it to
  `FastAPI(description=...)`.
- Set `_TAGS_METADATA` as a list of `{"name": ..., "description": ...}` dicts passed to
  `openapi_tags=`.
- The `lifespan` context manager needs a docstring explaining startup and shutdown behaviour.

---

## Logging

The API uses **structlog** for all structured logging.  Never use `print()` or
`logging.getLogger` directly in application code.

### Obtaining a logger

Import from `gm_shield.core.logging` at the top of every module that needs logging:

```python
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)
```

### Emitting events

Use **keyword arguments** for all structured context — never f-strings:

```python
# ✅ correct — fields are individually queryable
logger.info("ingestion_started", file_path=file_path)
logger.warning("no_text_extracted", file_path=file_path)
logger.error("text_extraction_failed", file_path=file_path, error=str(e))

# ❌ wrong — message is unstructured; impossible to filter/query
logger.info(f"Starting processing for {file_path}")
```

Choose **snake_case event names** that describe what happened, not status messages:

| Good | Avoid |
|---|---|
| `"ingestion_started"` | `"Starting processing..."` |
| `"sqlite_ok"` | `"Database is healthy"` |
| `"ollama_model_missing"` | `f"Model {name} not found"` |

### Log level guidance

| Level | When to use |
|---|---|
| `debug` | Detailed internal state useful during development only |
| `info` | Normal operational events (startup, healthy checks, job complete) |
| `warning` | Recoverable degradation (missing model, empty file, retried call) |
| `error` | Unrecoverable failure — typically just before raising an exception |

### Configuration

`configure_logging()` in `gm_shield/core/logging.py` is called **once** in
`main.py` at import time.  It honours two optional environment variables:

| Variable | Default | Options |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `console` | `console` (coloured), `json` (newline-delimited JSON) |

Set `LOG_FORMAT=json` in production / container environments so log aggregators
(e.g. CloudWatch, Loki) can parse fields natively.

---

## Testing rules

- Test framework: `pytest` (+ `pytest-asyncio`, `pytest-bdd`).
- All tests are **deterministic**: no real network calls, no real disk I/O unless using
  `tmp_path`, no sleeps unless polling async completion.
- Match test location to test type:

| What | Where |
|---|---|
| Pure-function unit logic | `tests/unit/test_<module>.py` |
| HTTP / integration behaviour | `tests/unit/test_<feature>.py` (using `TestClient`) |
| BDD / Gherkin scenarios | `tests/features/<scenario>.feature` + `tests/features/steps/` |

### Unit tests

Use `pytest` fixtures and `unittest.mock` utilities. Group tests by function under test;
name functions `test_<function>_<scenario>`:

```python
# tests/unit/test_knowledge_extraction.py

import pytest
from unittest.mock import MagicMock, patch
from gm_shield.features.knowledge.service import extract_text_from_file


@pytest.fixture
def mock_file_path(tmp_path):
    return tmp_path / "test_file.txt"


def test_extract_text_txt(mock_file_path):
    mock_file_path.write_text("Hello World", encoding="utf-8")
    text = extract_text_from_file(str(mock_file_path))
    assert text == "Hello World"


def test_extract_text_unsupported(tmp_path):
    bad_file = tmp_path / "test.exe"
    bad_file.touch()
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text_from_file(str(bad_file))


def test_extract_text_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("non_existent_file.txt")
```

### HTTP / integration tests (TestClient)

Use `TestClient` directly in the test file; override dependencies via
`app.dependency_overrides` scoped to a fixture:

```python
# tests/unit/test_knowledge_service.py

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from gm_shield.main import app

client = TestClient(app)


@pytest.fixture
def mock_queue():
    with patch("gm_shield.features.knowledge.router.get_task_queue") as mock:
        queue = AsyncMock()
        mock.return_value = queue
        queue.enqueue.return_value = "mock_task_id"
        yield queue


def test_add_knowledge_source(mock_queue):
    response = client.post(
        "/api/v1/knowledge/",
        json={"file_path": "/path/to/test.pdf", "description": "Test PDF"},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "mock_task_id"
    assert data["status"] == "pending"
    assert "Processing started" in data["message"]

    # Verify the background task was enqueued with the correct path
    mock_queue.enqueue.assert_called_once()
    _, kwargs = mock_queue.enqueue.call_args
    assert "/path/to/test.pdf" in mock_queue.enqueue.call_args[0]
```

### Async tests

Mark with `@pytest.mark.asyncio`. Patch all I/O (database, embeddings, external HTTP):

```python
@patch("gm_shield.features.knowledge.service.extract_text_from_file")
@patch("gm_shield.features.knowledge.service.get_embedding_model")
@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_process_knowledge_source(mock_chroma, mock_embed, mock_extract):
    mock_extract.return_value = "Chunk1 Chunk2 Chunk3"

    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1], [0.2], [0.3]])
    mock_embed.return_value = mock_model

    mock_collection = MagicMock()
    mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

    result = await process_knowledge_source("/path/to/test.txt")

    assert "Processed 3 chunks" in result
    mock_extract.assert_called_with("/path/to/test.txt")
    mock_collection.add.assert_called_once()
```

### BDD / Gherkin tests (pytest-bdd)

Feature files live in `tests/features/`. Use plain English scenarios with `Feature`,
`Scenario`, `Given`/`When`/`Then`/`And`:

```gherkin
# tests/features/knowledge_ingestion.feature

Feature: Knowledge ingestion

  Scenario: Successful document ingestion
    Given the API is running
    And a valid PDF file exists at "/data/monster-manual.pdf"
    When I POST to "/api/v1/knowledge/" with the file path
    Then the response status code should be 202
    And the response body should contain a "task_id"
    And the response "status" should be "pending"

  Scenario: Unsupported file type rejected
    Given the API is running
    When I POST to "/api/v1/knowledge/" with file_path "/data/report.exe"
    Then the response status code should be 422
```

Step definitions live in `tests/features/steps/<feature>_steps.py` and use
`@given`, `@when`, `@then` decorators from `pytest_bdd`:

```python
# tests/features/steps/knowledge_ingestion_steps.py

from pytest_bdd import given, when, then, parsers
from fastapi.testclient import TestClient
from gm_shield.main import app


@given("the API is running")
def api_client():
    return TestClient(app)


@when(parsers.parse('I POST to "{endpoint}" with the file path'), target_fixture="response")
def post_knowledge(api_client, endpoint, mock_queue):
    return api_client.post(endpoint, json={"file_path": "/data/monster-manual.pdf"})


@then(parsers.parse("the response status code should be {code:d}"))
def check_status_code(response, code):
    assert response.status_code == code


@then('the response body should contain a "task_id"')
def check_task_id(response):
    assert "task_id" in response.json()
```

### Fixtures (conftest.py)

Use the shared fixtures in `tests/conftest.py`:
- `db_session` — in-memory SQLite session, rolled back after each test.
- `client` — `TestClient` with `get_db` overridden to `db_session`.

For ad-hoc dependency overrides in a single test file, scope the override to a `pytest.fixture`
and clean up with `app.dependency_overrides = {}` in a `yield` fixture.

---

## Testing commands

| Command | What it runs |
|---|---|
| `cd apps/api && uv run python -m pytest` | All tests |
| `cd apps/api && uv run python -m pytest tests/features -q` | BDD feature tests only |
| `cd apps/api && uv run python -m pytest tests/unit -q` | Unit tests only |
| `cd apps/api && uv run python -m pytest -k "knowledge" -q` | Tests matching a keyword |

---

## Workflow examples

### Adding a new endpoint in a slice

1. **Model** — add request/response Pydantic classes in `gm_shield/features/<slice>/models.py`
   (follow Field + docstring rules above).
2. **Service** — add business logic in `gm_shield/features/<slice>/service.py` with full
   Google-style docstrings.
3. **Router** — add route with `summary`, `description`, and `responses` in
   `gm_shield/features/<slice>/routes.py` (or `router.py`).
4. **Register** — include the router in `gm_shield/main.py`.
5. **Tests**:
   - Unit test for the service function in `tests/unit/test_<slice>_service.py`.
   - HTTP test for the endpoint in `tests/unit/test_<slice>.py`.
   - BDD scenario in `tests/features/<slice>.feature`.

### Extracting a reusable helper to `shared/`

1. Move the helper into `gm_shield/shared/<subpackage>/`.
2. Update all importing slices.
3. Add a unit test in `tests/unit/test_<helper>.py`.
4. Add a Google-style docstring with `Args:`, `Returns:`, and `Raises:`.

### Adding a new BDD scenario

1. Open (or create) `tests/features/<feature>.feature`.
2. Add a `Scenario:` block with `Given`/`When`/`Then` steps.
3. Implement any missing step definitions in `tests/features/steps/<feature>_steps.py`.
4. Run `cd apps/api && uv run python -m pytest tests/features -q` to verify.
