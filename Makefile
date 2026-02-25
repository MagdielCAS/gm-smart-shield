.PHONY: help setup api-setup web-setup run-api web-dev test api-test web-test web-test-e2e web-test-bdd lint api-lint web-lint lint-fix api-lint-fix web-lint-fix format api-format web-format web-build docker-up docker-down docker-logs docker-build

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: api-setup web-setup ## Setup dependencies for both API and Web

api-setup: ## Setup API dependencies
	@echo "Setting up API dependencies..."
	cd apps/api && uv sync
	@echo "Installing lefthook..."
	./apps/api/.venv/bin/lefthook install || echo "Lefthook install failed (expected in some environments)"

web-setup: ## Setup Web dependencies
	@echo "Setting up Web dependencies..."
	cd apps/web && pnpm install

run-api: ## Run API server
	@echo "Running API..."
	cd apps/api && uv run uvicorn gm_shield.main:app --reload

web-dev: ## Run Web development server
	@echo "Running Web..."
	cd apps/web && pnpm dev

test: api-test web-test ## Run all tests (API and Web unit)

api-test: ## Run API tests
	@echo "Running API tests..."
	cd apps/api && uv run python -m pytest

web-test: ## Run Web unit tests
	@echo "Running Web unit tests..."
	cd apps/web && pnpm test

web-test-e2e: ## Run Web E2E tests
	@echo "Running Web E2E tests..."
	cd apps/web && pnpm test:e2e

web-test-bdd: ## Run Web BDD tests
	@echo "Running Web BDD tests..."
	cd apps/web && pnpm test:bdd

lint: api-lint web-lint ## Run all linters (API and Web)

lint-fix: api-lint-fix web-lint-fix ## Auto-fix lint errors in all apps

api-lint: ## Run API linter (ruff)
	@echo "Running API linter..."
	cd apps/api && uv run ruff check .

api-lint-fix: ## Auto-fix API lint errors (ruff --fix)
	@echo "Fixing API lint errors..."
	cd apps/api && uv run ruff check --fix .

format: api-format web-format ## Run formatters for all apps

api-format: ## Format API code (ruff format)
	@echo "Formatting API code..."
	cd apps/api && uv run ruff format .

docker-up: ## Start Docker services
	@echo "Starting Docker services..."
	docker compose up -d

docker-down: ## Stop Docker services
	@echo "Stopping Docker services..."
	docker compose down

docker-logs: ## Tail Docker logs
	@echo "Tailing Docker logs..."
	docker compose logs -f

docker-build: ## Build Docker images
	@echo "Building Docker images..."
	docker compose build
web-lint: ## Run Web linter (Biome)
	@echo "Running Web linter..."
	cd apps/web && pnpm lint

web-lint-fix: ## Auto-fix Web lint errors (Biome --write)
	@echo "Fixing Web lint errors..."
	cd apps/web && pnpm biome check --write .

web-format: ## Format Web code (Biome --write)
	@echo "Formatting Web code..."
	cd apps/web && pnpm biome format --write .

web-build: ## Build Web application
	@echo "Building Web..."
	cd apps/web && pnpm build
