# OpenMinds

**Open-source full-stack multi-human & multi-agent autonomous platform.**

A self-hostable control plane where humans and AI agents operate as first-class teammates. Distributed runner fleets, durable typed agents, visual workflows, real-time voice, mobile vision, multi-modal rendering, cryptographic isolation, and a skills marketplace — all under one evidence-first console.

> Systems that prove what happened.

## Why OpenMinds

Most platforms stop at chat or one-click remix. OpenMinds is built for autonomous production work:

- Multi-human + multi-agent squads with issue boards, review gates, and handoffs
- Distributed runner fleets with pod isolation, worktrees, and real-time PTY streaming
- Node-based pipeline generation (ComfyUI graphs + inference + mobile + agent + review DAGs)
- Durable typed agents (Pydantic AI) with checkpointing, evals, and structured outputs
- Real-time voice sessions, framebuffer streaming, and Mobile-Use vision drivers
- Zero-cost inference fallbacks, semantic routing, and self-healing scheduling
- Cryptographic guardrails, mTLS fleet certificates, secret scrubbing, and immutable ledgers
- Appwrite BaaS for ephemeral sessions and artifact vaults
- Multi-region schema sync, automated backups, and rate-limited multi-tenant pools
- Open skill publishing and marketplace without vendor lock-in

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Unified Console (Next.js)                                │
│ Board · Node Flows · Diagnostics · Assets · Terminal     │
└────────────────────────┬─────────────────────────────────┘
                         │ WebSocket · gRPC · REST
┌────────────────────────▼───────────────────────────────┐
│ Control Plane                                            │
│ Auth · Squads · Orchestration · Telemetry · PKI          │
└───────┬──────────────┬──────────────┬─────────────────────┘
        ▼              ▼              ▼
   Local Daemon   Runner Fleet   Durable Agents
   (BYO CLIs)     (Pods)         (Pydantic AI)
```

## Topics

`ai-agents` `multi-agent` `agent-swarm` `autonomous-agents` `self-hosted` `open-source` `pydantic-ai` `comfyui` `mobile-use` `durable-execution` `workflow-orchestration` `human-in-the-loop` `skills-marketplace` `mtls` `zero-trust` `rag` `voice-agents` `edge-computing` `evidence-systems` `codesbyfebin`

## Quick Start

```bash
git clone https://github.com/CodesbyFebin/Open-Human-Agents-Stack.git
cd Open-Human-Agents-Stack

# Apply schemas
psql -f database/schema_extensions.sql
psql -f database/multica_schema.sql
psql -f database/system_extensions.sql

# Bootstrap mTLS
chmod +x scripts/bootstrap_pki.sh
./scripts/bootstrap_pki.sh

# Launch
docker compose -f docker/docker-compose.prod.yml -f docker/docker-compose.extensions.yml up --build -d
```

## Core Engines

| Engine | Path | Purpose |
|--------|------|---------|
| Node Pipeline DAG | `backend/pipeline/node_pipeline.py` | Composable render + inference + agent + review graphs |
| ComfyUI Graph | `backend/pipeline/comfy_graph.py` | Multi-modal generation |
| Durable Worker | `agents/durable_worker.py` | Typed coding agents with isolation |
| Mobile Vision | `runners/mobile/vision_driver.py` | Bounding-box to tap translation |
| Appwrite Core | `backend/services/appwrite_core.go` | Session + artifact BaaS |
| Redis Event Mesh | `backend/services/event_mesh.go` | Cross-engine pub/sub |
| Multi-Region Syncer | `database/migrations/syncer.go` | Bytebase-style schema replication |
| Backup Engine | `backend/services/backup_engine.go` | pg_dump → Appwrite cron |
| Rate Limiter | `backend/api/rate_limiter.go` | Velocity + budget gates |
| PKI | `backend/pkg/security/pki.go` | mTLS CA + node certificates |

## Status

Production-oriented scaffolds for a fully functional autonomous platform. Control plane, schemas, node pipelines, security mesh, and operator consoles are resident and ready for live wiring.

Built by [CodesbyFebin](https://github.com/CodesbyFebin) · systems that prove what happened.
