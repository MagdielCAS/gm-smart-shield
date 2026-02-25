# AGENTS.md

## Repository context
- **Project:** GM Smart Shield (local-first AI assistant for tabletop GMs).
- **Current code focus:** Python API in `apps/api` (FastAPI + SQLite + ChromaDB).
- **Status:** pre-alpha; prioritize clear, incremental changes over broad refactors.

## Architecture overview (read before coding)
- Follow **vertical slices** (`docs/adr/0001-vertical-slices.md`):
  - Feature code belongs under `apps/api/gm_shield/features/<feature_name>/`.
  - Shared, cross-feature code belongs in `apps/api/gm_shield/shared/`.
  - Core app config/bootstrap belongs in `apps/api/gm_shield/core/` and `main.py`.
- Keep features loosely coupled; avoid importing feature internals across slices.
- Preserve local-first assumptions (no mandatory cloud dependencies for core behavior).

## Rules for adding features
1. Start with a new or existing slice in `features/`; avoid dumping feature logic into `main.py`.
2. Keep API contracts explicit (request/response schemas via Pydantic).
3. If logic is generic and reused by multiple slices, move it to `shared/`.
4. Prefer small PRs: routing + service + tests in the same change.
5. Update docs when behavior changes (`README.md`, `docs/TECHNICAL.md`, or ADRs as needed).

## Rules for testing
- Add/adjust tests with every functional change.
- Use the existing test split:
  - `apps/api/tests/unit/` for fast isolated logic tests.
  - `apps/api/tests/features/` for behavior/API flow tests (pytest-bdd).
- Default commands:
  - `make test` (repo root)
  - `cd apps/api && uv run python -m pytest`
- For new endpoints, include at least:
  - one success-path test,
  - one failure/validation-path test.

## Practical conventions for agents
- Keep edits minimal and localized.
- Do not introduce new frameworks/tools unless clearly justified.
- Reuse existing patterns in `apps/api/tests/conftest.py` for DB and client fixtures.
- When uncertain, choose consistency with existing code over novelty.
