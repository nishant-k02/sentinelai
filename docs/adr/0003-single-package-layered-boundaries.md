# ADR-0003: One `src/sentinelai` package, boundaries enforced by import-linter

- **Status:** Accepted
- **Date:** 2026-09-06

## Context

ADR-0001 commits to a modular monolith, which only works if "module
boundary" means something mechanically enforced, not just a naming
convention reviewers are trusted to catch.

## Decision

One `src/sentinelai` package: `platform/` (lowest layer — config, logging,
tracing, error types, Redis/Postgres/Kafka factories), `modules/` (bounded
contexts, e.g. `organization/`), `api/` and `worker/` (entrypoints/adapters,
same layer). import-linter's `layers` contract fails `make lint` and CI on
any import running the wrong direction (e.g. `platform` importing `api`).

## Alternatives considered

- **Separate `apps/api`, `apps/worker` Python packages/pyproject.tomls** —
  rejected for now: adds packaging overhead disproportionate to the current
  size. Revisit if the two processes' dependency sets diverge significantly.
- **Code-review-only discipline, no tooling** — rejected: doesn't hold under
  time pressure, and defeats the purpose of calling the boundary "enforced."

## Trade-offs

API and worker share one dependency set — the worker pays the image-size
cost of any heavy library the API needs, and vice versa. The layering
contract in `pyproject.toml` needs a manual update whenever a new top-level
package is added (already missed once during Phase 0.4, caught immediately
by the next `make lint` run).

## Consequences

`uv run lint-imports` is a real, enforced step of `make lint` and CI. A
forbidden import fails the build immediately, not in review — this is what
"enforced" means mechanically, as opposed to "documented."
