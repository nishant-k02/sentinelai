# SentinelAI

[![CI](https://github.com/nishant-k02/sentinelai/actions/workflows/ci.yml/badge.svg)](https://github.com/nishant-k02/sentinelai/actions/workflows/ci.yml)

Intelligent incident-detection, root-cause analysis, and automated-remediation
platform for distributed systems — a from-scratch, production-shaped project
covering system design, distributed systems, AI/ML, and DevOps end to end.

SentinelAI watches a fleet of services, detects anomalies, opens a structured
incident, runs an LLM-agent investigation grounded in real evidence (metrics,
logs, deploys, runbooks via RAG), produces ranked root-cause hypotheses with
citations, and — with human approval — executes bounded, audited remediations.

## Status

**Milestone 0 (foundation) — complete.** A modular-monolith API, an async
worker, Postgres, Redis, Kafka (Redpanda), OpenTelemetry tracing, a Next.js
frontend with contract-tested types, Docker images, and a five-job CI
pipeline. No incident-detection domain logic exists yet — that begins at
Milestone 1.

- [`docs/HLD.md`](docs/HLD.md) — requirements and target architecture
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — what's built today
- [`docs/adr/`](docs/adr/) — why it's built this way

## Local development

Prerequisites: `uv`, Node 24, `pnpm` (via corepack), Docker Desktop.

```bash
make install && make web-install   # dependencies
make up                            # Postgres, Redis, Redpanda, Jaeger
make migrate                       # apply database migrations
make check                         # lint, type-check, unit tests
make test-integration              # integration tests (needs `make up`)
```

Run it:

```bash
uv run uvicorn sentinelai.main:app --reload   # API      -> localhost:8000/docs
make worker                                    # worker (separate terminal)
make web-dev                                   # frontend -> localhost:3000
```

Traces: `http://localhost:16686` (Jaeger).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branching, commit conventions,
and PR expectations.
