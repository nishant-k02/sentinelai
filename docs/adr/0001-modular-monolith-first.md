# ADR-0001: Start as a modular monolith, not microservices

- **Status:** Accepted
- **Date:** 2026-09-06

## Context

SentinelAI's target architecture (see docs/HLD.md) eventually involves several
independently-scalable subsystems: detection, RAG, an AI investigation agent,
a remediation engine. The team is one person; the domain model (what an
Incident is, how severity is assigned, how alerts correlate) is unproven and
will change shape repeatedly while it's being built.

## Decision

Ship one deployable Python package (`sentinelai`) containing `platform/`
(cross-cutting infra), `modules/` (bounded contexts), and `api/`/`worker/`
(entrypoints), with internal module boundaries enforced by import-linter —
not separate services.

## Alternatives considered

- **Microservices from day one** — rejected. Network calls between module
  boundaries that haven't stabilized yet buy distributed-systems failure
  modes (partial failure, network latency, versioning across deploys) with
  no corresponding benefit, since nothing yet needs independent scaling or
  independent deployment.
- **No enforced boundaries, one flat module** — rejected. Without automated
  enforcement, module boundaries erode under time pressure; the entire
  reason to organize the code this way disappears.

## Trade-offs

No independent deployability or failure isolation between subsystems yet - a
bug in one module can take down the whole process. All modules share one
dependency set, one deploy cadence, one restart.

## Consequences

Extracting a subsystem into its own service (Architecture Evolution Phase 4)
becomes a deliberate, well-scoped refactor rather than a rewrite, because the
module's boundary - its imports, its public interface — is already explicit
and enforced in code today.
