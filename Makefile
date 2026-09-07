.PHONY: install fmt lint typecheck test check

install:  ## Sync dependencies into .venv from uv.lock
	uv sync

fmt:  ## Auto-format and auto-fix
	uv run ruff format .
	uv run ruff check --fix .

lint:  ## Check formatting + lint rules (no changes)
	uv run ruff format --check .
	uv run ruff check .

typecheck:  ## Static type checking
	uv run mypy

test:  ## Run the test suite
	uv run pytest

check: lint typecheck test  ## Everything CI runs
