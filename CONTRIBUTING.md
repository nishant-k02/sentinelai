# Contributing

## Branching

- `main` is always deployable. Never commit to it directly.
- Branch per unit of work:
  - `feature/<name>` — new capability (e.g. `feature/incident-service`)
  - `fix/<name>` — bug fix
  - `chore/<name>` — tooling, infra, docs, refactor with no behaviour change
- Open a PR into `main`. CI must be green. Squash-merge.

## Commits — Conventional Commits

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`.

Examples:

- feat(incident): add severity rules engine
- fix(detection): reset EWMA baseline on service redeploy
- chore(bootstrap): scaffold repo, tooling, CI
- docs(adr): record decision to start as a modular monolith

Subject: imperative mood, lower case, no trailing period, <= 72 chars.
Body (optional): what and why, not how. Wrap at 72.

## Pull requests

Fill in `.github/pull_request_template.md`: context, what changed, how tested,
screenshots if UI, and the ADR link if the PR makes an architectural decision.
