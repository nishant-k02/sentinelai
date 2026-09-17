# ADR-0006: Frontend types generated from the backend's OpenAPI schema

- **Status:** Accepted
- **Date:** 2026-09-14

## Context

TypeScript and Python are two separate type systems describing the same API
contract. Left to hand-maintenance, they drift the moment one side changes
without the other — silently, since nothing catches it until runtime.

## Decision

`openapi-typescript` generates `web/src/lib/api-types.gen.ts` from the
running API's `/openapi.json`. The generated file is committed. A CI job
(`contract-drift`) regenerates it against a live API and fails the build if
the committed version differs.

## Alternatives considered

- **Hand-written TypeScript interfaces mirroring the Pydantic models** —
  rejected: drifts silently; nothing forces the two definitions to stay in
  sync.
- **A shared schema language (protobuf/gRPC) across both stacks** — rejected
  as overkill for a JSON REST API, where FastAPI already produces a complete,
  accurate OpenAPI document for free.

## Trade-offs

The generated file isn't automatically *kept current* — `make gen-api-types`
must be run by hand after a backend contract change. CI only automatically
*checks* it's current, it doesn't fix it for you.

## Consequences

A backend response-shape change becomes a TypeScript compile error at the
exact call site that assumed the old shape, instead of a runtime `undefined`
bug discovered in the browser days later.
