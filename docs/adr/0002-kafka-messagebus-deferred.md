# ADR-0002: Kafka (via Redpanda) now; a MessageBus abstraction deferred to M4

- **Status:** Accepted
- **Date:** 2026-09-12

## Context

The target architecture is event-driven, and a specific goal of this project
is hands-on understanding of Kafka semantics — partitions, offsets, consumer
groups, delivery guarantees. At this stage, only one smoke-test topic exists;
no real domain events are published or consumed yet.

## Decision

Use `aiokafka` directly against Redpanda (Kafka-wire-protocol compatible, no
ZooKeeper/JVM, trivial to run locally) for now. Do not build a `MessageBus`
interface abstracting the broker until M4, when multiple real modules need
to publish and consume actual domain events.

## Alternatives considered

- **GCP Pub/Sub** — rejected for now. It hides partitions, offsets, and
  consumer-group mechanics behind a simpler API — exactly what this project
  wants to learn directly. Revisit for production cost/ops trade-offs later;
  the eventual `MessageBus` interface is what makes that switch possible
  without touching call sites.
- **Building the MessageBus interface now** — rejected as premature
  abstraction: with one topic and no real producers/consumers besides a
  smoke test, there is nothing yet to abstract *over*.

## Trade-offs

`platform/messaging.py` and the worker are coupled directly to aiokafka's
API. Swapping brokers today means editing call sites, not a config value.

## Consequences

When M4 introduces real domain events (`IncidentCreated`, etc.) across
multiple modules, the `MessageBus` interface gets designed against actual,
multiple use cases — likely a better interface than one designed speculatively
against a single smoke-test topic would have been.
