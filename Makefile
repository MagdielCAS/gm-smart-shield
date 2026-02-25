.PHONY: help setup api-setup web-setup run-api web-dev test api-test web-test web-test-e2e web-test-bdd lint api-lint web-lint web-build docker-up docker-down docker-logs docker-build

help:
	@echo "Available commands:"
	@echo "  setup         - Setup dependencies for both API and Web"
	@echo "  api-setup     - Setup API dependencies"
	@echo "  web-setup     - Setup Web dependencies"
	@echo "  run-api       - Run API server"
	@echo "  web-dev       - Run Web development server"
	@echo "  test          - Run all tests (API and Web unit)"
	@echo "  api-test      - Run API tests"
	@echo "  web-test      - Run Web unit tests"
	@echo "  web-test-e2e  - Run Web E2E tests"
	@echo "  web-test-bdd  - Run Web BDD tests"
	@echo "  lint          - Run linters for both API and Web"
	@echo "  api-lint      - Run API linter"
	@echo "  web-lint      - Run Web linter"
	@echo "  web-build     - Build Web application"
	@echo "  docker-up     - Start Docker services"
	@echo "  docker-down   - Stop Docker services"
	@echo "  docker-logs   - Tail Docker logs"
	@echo "  docker-build  - Build Docker images"

setup: api-setup web-setup

api-setup:
	@echo "Setting up API dependencies..."
	cd apps/api && uv sync
	@echo "Installing lefthook..."
	./apps/api/.venv/bin/lefthook install || echo "Lefthook install failed (expected in some environments)"

web-setup:
	@echo "Setting up Web dependencies..."
	cd apps/web && pnpm install

run-api:
	@echo "Running API..."
	cd apps/api && uv run uvicorn gm_shield.main:app --reload

web-dev:
	@echo "Running Web..."
	cd apps/web && pnpm dev

test: api-test web-test

api-test:
	@echo "Running API tests..."
	cd apps/api && uv run python -m pytest

web-test:
	@echo "Running Web unit tests..."
	cd apps/web && pnpm test

web-test-e2e:
	@echo "Running Web E2E tests..."
	cd apps/web && pnpm test:e2e

web-test-bdd:
	@echo "Running Web BDD tests..."
	cd apps/web && pnpm test:bdd

lint: api-lint web-lint

api-lint:
	@echo "Running API linter..."
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
web-lint:
	@echo "Running Web linter..."
	cd apps/web && pnpm lint

web-build:
	@echo "Building Web..."
	cd apps/web && pnpm build

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
