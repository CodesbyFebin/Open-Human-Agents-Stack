# AGENTS.md — OpenMinds

This repository is a scaffold for a multi-human / multi-agent control plane.

## Layout
- `backend/` — FastAPI control plane (Python). Entry: `backend/main.py`
- `ui/` — Next.js operator console
- `database/migrations/` — versioned SQL
- `tests/` — pytest
- `docker/` — Compose files
- `scripts/` — migrate, backup, PKI bootstrap

## Rules for agents
- Do not claim production readiness. This is a scaffold.
- Privileged endpoints require Bearer auth (`backend/auth.py`).
- Human review gates must remain fail-closed.
- New migrations go in `database/migrations/` as numbered SQL.
- Add or update a test when changing gate or auth behavior.
- Do not commit secrets or `next-env.d.ts`.

## Commands
- `make test` — run pytest
- `make up` — docker compose
- `make migrate` — apply SQL migrations
