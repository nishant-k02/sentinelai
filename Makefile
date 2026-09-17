.PHONY: install fmt lint typecheck test test-integration test-all check up down logs migrate migration \
	worker web-install web-dev web-lint web-typecheck web-test web-build gen-api-types

install:  ## Sync dependencies into .venv
	uv sync

fmt:  ## Auto-format and auto-fix
	uv run ruff format .
	uv run ruff check --fix .

lint:  ## Formatting + lint + import-boundary checks (no changes)
	uv run ruff format --check .
	uv run ruff check .
	uv run lint-imports

typecheck:  ## Static type checking
	uv run mypy

test:  ## Fast tests only (no Docker needed)
	uv run pytest -m "not integration"

test-integration:  ## Integration tests (run `make up` first)
	uv run pytest -m integration

test-all:  ## Every test (needs infra up)
	uv run pytest

check: lint typecheck test web-lint web-typecheck web-test  ## What runs on every change

up:  ## Start local infra and wait until healthy
	docker compose -f infra/compose/docker-compose.yml up -d --wait

down:  ## Stop local infra (data volume is kept)
	docker compose -f infra/compose/docker-compose.yml down

logs:  ## Follow infra logs
	docker compose -f infra/compose/docker-compose.yml logs -f

migrate:  ## Apply all pending migrations
	uv run alembic upgrade head

migration:  ## Autogenerate a migration:  make migration m="add users table"
	uv run alembic revision --autogenerate -m "$(m)"

worker:  ## Run the worker process (Ctrl+C for graceful shutdown)
	uv run python -m sentinelai.worker

web-install:  ## Install frontend dependencies
	cd web && pnpm install

web-dev:  ## Run the frontend dev server
	cd web && pnpm dev

web-lint:  ## Format-check + lint the frontend
	cd web && pnpm format:check && pnpm lint

web-typecheck:  ## Type-check the frontend
	cd web && pnpm typecheck

web-test:  ## Run frontend tests
	cd web && pnpm test

web-build:  ## Production build of the frontend
	cd web && pnpm build

gen-api-types:  ## Regenerate web/src/lib/api-types.gen.ts (needs the API running)
	cd web && pnpm gen:api-types

docker-build-api:  ## Build the shared API/worker image
	docker build -f infra/docker/api.Dockerfile -t sentinelai-api:local .

docker-build-web:  ## Build the web image
	docker build -f infra/docker/web.Dockerfile -t sentinelai-web:local web

docker-build: docker-build-api docker-build-web  ## Build all images
