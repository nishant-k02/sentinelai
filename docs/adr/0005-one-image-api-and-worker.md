# ADR-0005: One container image, shared by the API and the worker

- **Status:** Accepted
- **Date:** 2026-09-16

## Context

The API and worker are the same Python package (per ADR-0003); a container
image needs to be built for each, and they need to be decided as one image
or two.

## Decision

A single `infra/docker/api.Dockerfile` produces one image. Which process
runs — `uvicorn sentinelai.main:app` or `python -m sentinelai.worker` — is
chosen by the container's command at run time, not by building a separate
image per process.

## Alternatives considered

- **Two separate Dockerfiles/images** — rejected: would duplicate the entire
  dependency-install layer for an identical dependency set, doubling build
  time and registry storage for zero isolation benefit today.

## Trade-offs

Can't independently slim one process's image if their dependencies diverge —
currently a non-issue since they're identical. Worth revisiting only if that
changes materially.

## Consequences

One image to build, scan, and version in CI/CD. Kubernetes (Phase M12) will
define the API and worker as separate Deployments built from this same
image with different commands — exactly the local `docker run` override,
just declared in a manifest instead of a shell command.
