.PHONY: setup run-api test lint docker-up docker-down docker-logs docker-build

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

docker-up:
	@echo "Starting Docker services..."
	docker compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker compose down

docker-logs:
	@echo "Tailing Docker logs..."
	docker compose logs -f

docker-build:
	@echo "Building Docker images..."
	docker compose build
