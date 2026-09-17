# High-Level Design

This is the target system and the plan to get there. For what's actually
built right now, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Vision

An AI-native incident management platform: detect anomalies in a fleet of
services, open a structured incident, run an autonomous investigation
grounded in real evidence (metrics, logs, deploys, runbooks via RAG), and
propose — or with approval, execute — bounded remediation. See the project's
design discussion for the full product rationale; this document tracks
requirements and architecture as they solidify through implementation.

## Core functional requirements

- Ingest metrics/logs/deployments per service; detect anomalies (statistical
  first, ML models post-MVP) behind a swappable `Detector` interface.
- Correlate related alerts into incidents; assign severity; maintain an
  auditable incident state machine and timeline.
- Collect evidence (metrics, logs, deploys, health) into a bounded
  investigation context.
- RAG over runbooks and historical incidents with citations on every claim.
- An LLM investigation agent with a permissioned, read-only tool set,
  producing root-cause hypotheses with a composite confidence score.
- A remediation engine: a fixed catalog of commands, never arbitrary
  execution, gated by authorization + approval + audit + rollback.
- OAuth2/JWT auth, RBAC, per-organization data isolation, full audit log.

## Non-functional requirements

| Attribute | Target |
|---|---|
| Availability | API 99.9%; AI investigation 99.0% (degrades gracefully) |
| Latency | API reads p95 < 200ms; MTTD < 60s; AI investigation p90 < 3min |
| Throughput | 1k events/min at MVP, with an explicit scaling plan to 1M/min |
| Consistency | Strong for incident state; eventual for dashboards/search |
| Durability | No loss of committed events; RPO <= 5min on the database |
| Security | TLS everywhere, least privilege, tenant isolation, full audit |
| Observability | RED/USE metrics, structured logs, traces, all correlated |

## Target architecture (evolution, not a leap)

1. **Modular monolith** (M0 — done) — one deployable, enforced boundaries.
2. **Async workers** (M0 — done) — detection/investigation off the request path.
3. **Event-driven architecture** (M4) — real domain events, outbox, DLQ,
   idempotent consumers.
4. **Service extraction** (M4+) — ML and AI services split out once scaling
   or isolation needs are real, not speculative.
5. **Kubernetes** (M12) — self-healing, autoscaling, rolling/canary deploys.
6. **Full observability** (M10) — OTel Collector, SLO dashboards, alerting.
7. **Load testing, failure injection, cost optimization** (M14).

## Roadmap

| Milestone | Delivers |
|---|---|
| M0 (done) | Modular monolith skeleton, Postgres/Redis/Kafka, tracing, CI, Docker |
| M1 | Service registry, metric/log ingestion API, DB schema v1 |
| M2 | Statistical anomaly detection behind a `Detector` interface |
| M3 | Incident domain: state machine, severity, correlation, timeline |
| M4 | Real event-driven architecture: outbox, idempotent consumers, DLQ |
| M5 | Evidence collection service |
| M6 | RAG pipeline: ingest, chunk, embed (pgvector), retrieve, cite |
| M7 | LLM investigation agent: tool registry, permissions, structured output |
| M8 | Remediation engine: Command pattern, approvals, audit, rollback |
| M9 | Frontend dashboard: incidents, AI panel, service health, runbooks |
| M10 | Full observability: OTel Collector, SLOs, alerting |
| M11 | Real ML detection: sklearn models, evaluation harness, drift |
| M12 | Kubernetes + Helm |
| M13 | Terraform + GCP + CI/CD to staging/prod |
| M14 | Failure injection, load testing, cost optimization |
| M15+ | Postmortem generation, knowledge loop, further service extraction |
