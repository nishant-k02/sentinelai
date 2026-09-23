# API Reference

The source of truth for the exact request/response shape is always the live
OpenAPI document (`/docs` for the interactive UI, `/openapi.json` for the
raw schema) — FastAPI generates it from the same Pydantic models used here.
This document is the *why* behind the conventions, not a duplicate of the
schema.

## Conventions

- **Base path:** all resource endpoints are versioned under `/v1`.
- **Errors:** every non-2xx response has the shape `{"error": {"code": str, "message": str}}`.
  `code` is a stable, machine-readable string (`not_found`, `conflict`,
  `validation_error`, `rate_limit_exceeded`, `internal_error`) — match on
  `code`, never on `message` text.
- **Creates:** every `POST` that creates a resource returns `201` with a
  `Location` header pointing at the new resource.
- **Telemetry is append-only:** metrics, logs, and deployments have no
  `PUT`/`PATCH`/`DELETE` — they're never edited or removed through the API.
- **Auth:** none yet. `organization_id` is a client-supplied field on
  writes — any caller can act on any organization. This is acceptable only
  because nothing is deployed; it is the first thing the upcoming Auth
  milestone must close, moving `organization_id` from the request body to
  a claim derived from an authenticated principal.

## Services

### `POST /v1/services`

Registers a service.

**Request:** `{ organization_id: uuid, name: string, environment: "development"|"staging"|"production" }`

**Responses:**
- `201` — `Location: /v1/services/{id}`, body is the created service.
- `404 not_found` — `organization_id` doesn't reference a real organization.
- `409 conflict` — a service with this `name` already exists in this organization.
- `422 validation_error` — malformed body (missing/wrong-typed field).

### `GET /v1/services/{id}`

- `200` — the service.
- `404 not_found` — no such service.

### `GET /v1/services`

**Query params:** `organization_id` (required), `environment` (optional filter),
`limit` (default 50, max 200), `offset` (default 0).

**Response:** `{ items: Service[], total: int, limit: int, offset: int }`

Uses **offset pagination** — appropriate here because the list is small,
human-browsed, and "jump to page N" is a reasonable thing to want. Contrast
with metrics below.

## Ingestion

All three endpoints below live under `/v1/services/{service_id}/...` and
share one rule: `service_id` must reference a real service, or the response
is `404 not_found`. Metrics and logs are rate-limited per service
(`429 rate_limit_exceeded`); deployments are not — they're rare,
human/CI-triggered events, not a volume-abuse surface.

### `POST /v1/services/{service_id}/metrics`

**Request:** `{ metric_name: string, value: number, recorded_at: datetime }`
→ `201`, `Location` header.

### `GET /v1/services/{service_id}/metrics`

**Query params:** `metric_name` (optional filter), `cursor` (optional,
opaque), `limit` (default 100, max 500).

**Response:** `{ items: MetricSample[], next_cursor: string | null }`

Uses **keyset (cursor) pagination**, not offset — this list is
unboundedly large, always consumed front-to-back, and "page 50" is never a
meaningful request. `next_cursor` is `null` once there are no more rows;
pass it back as `?cursor=...` to continue. A cursor from one service's list
is meaningless (and rejected as `422 validation_error` if malformed) against
another — it encodes a `(recorded_at, id)` position, not a page number.

### `POST /v1/services/{service_id}/logs`

**Request:** `{ level: "debug"|"info"|"warning"|"error"|"critical", message: string, attributes?: object, recorded_at: datetime }`
→ `201`, `Location` header. No list endpoint yet — nothing consumes one (arrives with the M9 dashboard).

### `POST /v1/services/{service_id}/deployments`

**Request:** `{ version: string, commit_sha: string, deployed_by: string, deployed_at: datetime }`
→ `201`, `Location` header. No list endpoint yet, same reason as logs.

## Platform endpoints (Milestone 0)

- `GET /healthz` — liveness, no dependencies checked.
- `GET /readyz` — readiness; `200` with `checks: {postgres, redis}` when
  healthy, `503` when either is down.
- `GET /metrics` — Prometheus scrape target.

## A documented bug, on purpose

`POST /v1/services` originally let a client-supplied `organization_id` that
didn't exist reach Postgres, surfacing as an unhandled `500`. Caught during
Milestone 1 acceptance testing — every automated test up to that point
happened to create a real organization first, so the gap was invisible to
the whole suite until the API was actually run standalone and hit by hand.
Fixed by checking existence in `register_service` before touching the
database (see `docs/adr` if this pattern recurs enough to warrant one).
Worth remembering as the concrete answer to "why bother manually
smoke-testing an API that has full test coverage" — the tests were right;
they collectively didn't cover this.
