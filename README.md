# SentinelAI

Intelligent incident detection, root-cause analysis, and automated remediation for distributed systems.

SentinelAI watches a fleet of services, detects anomalies before humans notice, opens a structured
incident, runs an LLM-agent investigation (grounded in metrics, logs, deploys, and RAG over runbooks),
produces ranked root-cause hypotheses with citations and a confidence score, and — with human approval —
executes bounded, audited remediations.

## Status

Milestone 0: foundation & walking skeleton. Not yet functional.

## Local development

Prerequisites: `uv`, Node 20, `pnpm`, Docker Desktop.

```bash
make install      # Python deps into .venv
make up           # start Postgres, Redis, Redpanda, observability stack
make migrate      # apply database migrations
make test         # run the test suite
uv run uvicorn sentinelai.main:app --reload   # API on http://localhost:8000
```
