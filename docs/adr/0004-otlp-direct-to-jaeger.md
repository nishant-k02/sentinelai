# ADR-0004: Export traces via OTLP directly to Jaeger; no Collector yet

- **Status:** Accepted
- **Date:** 2026-09-15

## Context

The target observability architecture includes an OpenTelemetry Collector
for routing, processing, and fanning telemetry out to multiple backends. At
M0's scale — one API, one worker, no production traffic, one trace backend —
a Collector is a moving part with nothing yet to route between.

## Decision

The API, worker, and Next.js frontend export spans via OTLP/HTTP directly to
Jaeger's built-in OTLP receiver.

## Alternatives considered

- **OTel Collector fronting Jaeger from day one** — rejected: no current need
  for sampling policy, protocol translation, or multi-backend fan-out, which
  is what a Collector is for. Adding it now would be infrastructure with no
  job to do yet.
- **No tracing until real traffic exists** — rejected: instrumentation is far
  cheaper to add before business logic starts depending on request context
  (correlated logs, span attributes) than to retrofit later.

## Trade-offs

Adding a second signal (metrics) or a second trace backend later means
touching each service's exporter configuration individually instead of one
Collector config.

## Consequences

Phase M10 (full observability stack) is the natural point to introduce a
Collector — once there's an actual second signal and/or backend that
justifies the extra hop, not before.
