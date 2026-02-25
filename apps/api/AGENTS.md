# AGENTS.md (apps/api)

## Scope
These rules apply to all files under `apps/api/`.

## Code organization rules
- Package root: `apps/api/gm_shield/`.
- Keep **vertical-slice boundaries**:
  - `features/<slice>/` contains routes + slice logic.
  - `shared/` contains reusable cross-slice components (DB adapters, worker abstractions).
  - `core/` contains global configuration and app-level wiring.
- Avoid circular imports; depend inward on shared/core primitives.
- Keep endpoint modules thin; move non-trivial logic into slice-level service modules.
- Place new routers in slice folders and register from `gm_shield/main.py`.

## Specific test rules
- Test framework: `pytest` (+ `pytest-asyncio`, `pytest-bdd`).
- Use fixtures from `apps/api/tests/conftest.py`:
  - `client` for HTTP tests with dependency overrides.
  - `db_session` for DB-backed tests.
- Prefer deterministic tests:
  - no real network calls,
  - no sleeps unless polling async behavior (as in worker tests).
- Add tests in the matching location:
  - unit logic: `tests/unit/test_<unit>.py`
  - API behavior/features: `tests/features/...`
- For async queue/worker behavior, assert status transitions and final payload.

## Testing commands
- Full API tests:
  - `cd apps/api && uv run python -m pytest`
- Feature-only tests:
  - `cd apps/api && uv run python -m pytest tests/features -q`
- Unit-only tests:
  - `cd apps/api && uv run python -m pytest tests/unit -q`

## Examples
- **New endpoint in a slice**
  - Add route in `gm_shield/features/<slice>/routes.py`.
  - Add logic in `gm_shield/features/<slice>/service.py`.
  - Register router in `gm_shield/main.py`.
  - Add tests in `tests/features/` using `client`.

- **Reusable helper extracted from multiple slices**
  - Move helper into `gm_shield/shared/...`.
  - Update importing slices.
  - Add unit test in `tests/unit/` for the shared helper.
