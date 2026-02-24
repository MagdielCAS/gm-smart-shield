.PHONY: setup run-api test lint

setup:
	@echo "Setting up API dependencies..."
	cd apps/api && uv sync
	@echo "Installing lefthook..."
	./apps/api/.venv/bin/lefthook install || echo "Lefthook install failed (expected in some environments)"

run-api:
	@echo "Running API..."
	cd apps/api && uv run uvicorn gm_shield.main:app --reload

test:
	@echo "Running tests..."
	cd apps/api && uv run python -m pytest

lint:
	@echo "Running linter..."
	cd apps/api && uv run ruff check .
