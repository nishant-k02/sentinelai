# syntax=docker/dockerfile:1
# Shared runtime image for the API and the worker — same package, started
# with a different command. Build from the repo root:
#   docker build -f infra/docker/api.Dockerfile -t sentinelai-api:local .

FROM python:3.12-slim AS builder

# Grab just the `uv` binary from Astral's own image.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
# If this tag is stale, check https://github.com/astral-sh/uv/pkgs/container/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies FIRST, from only the lock/manifest files via bind mounts (not
# a full COPY — nothing here becomes an image layer). Docker reuses this
# layer for every build where pyproject.toml/uv.lock are unchanged, i.e.
# almost every commit that only touches application code.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Now the manifest files for real (not just bind-mounted) and the source,
# then install the project itself — this layer invalidates on every code
# change, but it's cheap: dependencies are already installed.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# ----------------------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --from=builder --chown=app:app /app/src ./src

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

USER app

# Documentation only — does not publish the port. `-p`/compose does that.
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# Default: the API. The worker overrides this at run time — see Step 6.
CMD ["uvicorn", "sentinelai.main:app", "--host", "0.0.0.0", "--port", "8000"]
