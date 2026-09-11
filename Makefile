.PHONY: install fmt lint typecheck test test-integration test-all check up down logs migrate migration

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

check: lint typecheck test  ## What runs on every change

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
