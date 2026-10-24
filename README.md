# OpenMinds — Open Human Agents Stack
<img width="2172" height="724" alt="Open Human Agents Command Center" src="https://github.com/user-attachments/assets/6e5908f3-4dc2-4d02-868d-da642f7b875b" />

**Open-source full-stack multi-human & multi-agent autonomous platform.**

A self-hostable control plane where humans and AI agents operate as first-class teammates. Distributed runner fleets, durable typed agents, visual workflows, real-time voice, mobile vision, multi-modal rendering, cryptographic isolation, and a skills marketplace — all under one evidence-first console.

> Systems that prove what happened.

Built by [CodesbyFebin](https://github.com/CodesbyFebin).

---

## Table of Contents

1. [Introduction](#introduction)
2. [Philosophy and Design Principles](#philosophy-and-design-principles)
3. [Why OpenMinds Exists](#why-openminds-exists)
4. [High-Level Architecture](#high-level-architecture)
5. [Core Components](#core-components)
6. [Detailed Engine Inventory](#detailed-engine-inventory)
7. [Data Model and Schemas](#data-model-and-schemas)
8. [Security Model](#security-model)
9. [Installation and Quick Start](#installation-and-quick-start)
10. [Configuration](#configuration)
11. [API Reference](#api-reference)
12. [Operator Console](#operator-console)
13. [Node-Based Pipeline Generation](#node-based-pipeline-generation)
14. [Mobile Vision and Device Control](#mobile-vision-and-device-control)
15. [Deployment](#deployment)
16. [Observability and Telemetry](#observability-and-telemetry)
17. [Skills Marketplace](#skills-marketplace)
18. [Development Guide](#development-guide)
19. [Roadmap](#roadmap)
20. [Contributing](#contributing)
21. [License](#license)

---

## Introduction

OpenMinds (also known as the Open Human Agents Stack) is a production-oriented open-source platform for orchestrating mixed human and AI agent workforces. It is designed for organizations and individuals who need more than chat interfaces or one-click remix marketplaces. The system treats agents as durable, observable, isolatable workers that can be scheduled, reviewed, handed off, and audited alongside human teammates.

The platform integrates capabilities drawn from and inspired by several open-source projects, including visual workflow engines, multi-machine runner systems, typed agent frameworks, team collaboration boards, and secure shell environments. Rather than remaining a collection of separate tools, OpenMinds unifies them under a single control plane, a shared data model, a cryptographic security layer, and an operator console.

The current codebase contains a functional full-stack scaffold: a FastAPI control plane, a Next.js operator console, Docker Compose definitions for local and production-style deployments, node-based pipeline orchestration, durable agent workers, mobile vision drivers, Appwrite-backed artifact storage, Redis event mesh primitives, multi-region schema synchronization, automated backups, rate limiting, and an mTLS public-key infrastructure. These components are ready for progressive live wiring.

OpenMinds is explicitly self-hostable. There is no requirement for a proprietary cloud. Operators may run the control plane on their own infrastructure, attach runner fleets on local machines or remote pods, and bring their own language-model keys or local inference endpoints.

## Philosophy and Design Principles

Several principles guide the architecture:

**Evidence first.** Every significant action should leave a durable, queryable trace. Trajectories, evals, schema migrations, certificates, and artifact uploads are recorded so that operators can reconstruct what happened.

**Humans and agents as peers.** Agents are not hidden behind chat bubbles. They appear on team boards, receive issue assignments, produce reviewable diffs, and can be handed off to humans or other agents.

**Isolation by default.** Runner environments, shell commands, and workspaces are sandboxed. Cryptographic guardrails, secret scrubbing, and mTLS node certificates reduce the blast radius of a compromised or misbehaving agent.

**Composable pipelines.** Work is expressed as directed acyclic graphs of nodes. Nodes may be inference calls, ComfyUI rendering graphs, mobile vision steps, durable code agents, human review gates, or storage operations. Pipelines are versionable and replayable.

**Zero-trust fleet.** Runners authenticate with short-lived certificates. The control plane does not assume network location equals trust.

**Open skill ecosystem.** Skills, workflows, and agent configurations can be published and reused without vendor lock-in. The marketplace layer is designed to be open.

**Progressive enhancement.** The scaffold is usable today. Additional engines (voice streaming, full gRPC terminal bridging, multi-region active-active) can be activated as operators require them.

These principles are reflected in the directory structure, the schema extensions, and the operator console modules.

## Why OpenMinds Exists

Many existing platforms optimize for discovery or single-turn interaction. Taku.ai, for example, emphasizes marketplace discovery and one-click remix of pre-built applications. Chat-centric tools excel at conversational assistance but provide limited structure for long-running, multi-agent, multi-human work.

OpenMinds targets a different set of use cases:

- Research swarms that gather, synthesize, and cite evidence across many sources, then hand results to human reviewers.
- Coding agent workforces that operate in isolated worktrees, produce structured diffs, and wait for approval before merging.
- Hybrid visual pipelines that combine language-model planning, image or video generation, and mobile-device verification.
- Durable long-running agents that survive process restarts through checkpointing and typed outputs.
- Multi-machine isolation where agents run on dedicated hardware with real-time terminal streaming back to the operator.
- Evidence-backed operations in which every decision, tool call, and cost is recorded.

By combining these capabilities under one control plane, OpenMinds reduces the operational burden of stitching together separate orchestration, rendering, mobile-control, and collaboration tools.

## High-Level Architecture

The system is organized in three primary tiers.

**Operator Console.** A Next.js application that provides the human interface. Modules include the Multica-style team board, node-flow canvas, diagnostics and circuit-breaker console, asset and certificate registry, mobile framebuffer stream, and an xterm.js terminal. The console communicates with the control plane over REST, WebSocket, and (planned) gRPC.

**Control Plane.** A FastAPI service that exposes health, pipeline execution, agent scheduling, and telemetry endpoints. It coordinates the node pipeline generator, durable workers, telemetry pipeline, voice session broker, marketplace, scheduler, and security services. Background engines written in Go handle Appwrite sessions, event mesh publication, backup, rate limiting, schema synchronization, and certificate signing.

**Execution Layer.** Local daemons that wrap existing CLIs, distributed runner fleets that provide isolated pods and worktrees, and durable typed agents implemented with Pydantic AI. Mobile vision drivers translate normalized coordinates into device taps. ComfyUI graph executors queue multi-modal rendering jobs.

A simplified view:

```
┌────────────────────────────────────────────────────────────┐
│ Unified Console (Next.js)                                  │
│ Board · Node Flows · Diagnostics · Assets · Terminal       │
└────────────────────────┬───────────────────────────────────┘
                         │ WebSocket · gRPC · REST
┌────────────────────────▼───────────────────────────────────┐
│ Control Plane                                              │
│ Auth · Squads · Orchestration · Telemetry · PKI            │
└───────┬──────────────┬──────────────┬──────────────────────┘
        ▼              ▼              ▼
   Local Daemon   Runner Fleet   Durable Agents
   (BYO CLIs)     (Pods)         (Pydantic AI)
```

State is stored in PostgreSQL. Transient coordination and pub/sub use Redis. Object storage and ephemeral sessions are delegated to Appwrite when configured. Certificates and private keys are generated by the PKI bootstrap script and signed by the control-plane security package.

## Core Components

### Control Plane Entry

The FastAPI application in `backend/main.py` is the primary HTTP surface. It currently exposes:

- `GET /health` — returns operational status, service name, and version.
- `POST /pipeline/run` — accepts a pipeline request (name, optional prompt, seed) and invokes the node pipeline generator with an example agent-swarm graph.
- `POST /agent/code` — accepts a coding task description and workspace path, returning a task identifier and acceptance status.
- `GET /telemetry/summary` — returns a lightweight summary of active runners, circuit status, daily cost, and trajectory count.

CORS is enabled for local development. The application is designed to be extended with additional routers for voice, marketplace, and Multica board operations.

### Operator Console Shell

The Next.js entry point (`ui/pages/index.tsx`) mounts `ResponsiveConsoleShell`. Supporting components include:

- `UnifiedConsoleShell.tsx` and `ResponsiveConsoleShell.tsx` — layout and module switching.
- `MulticaBoard.tsx` — kanban-style board for human and agent issues.
- `WorkflowCanvas.tsx` — visual representation of node graphs.
- `OmniConsole.tsx` and `CircuitDiagnosticConsole.tsx` — telemetry and circuit-breaker views.
- `AgentDiffVisualizer.tsx` — line-level diff review with approve/reject actions.
- `MobileFrameBufferStream.tsx` and `MobileGenerationCanvas.tsx` — device screen streaming and generation workflows.
- `CertificateRegistryDashboard.tsx` — display of runner leases and cryptographic status.
- `XtermTerminalWrapper.tsx` — terminal attachment for live runner sessions.

Styling follows a dark evidence-console aesthetic with monospace typography.

### Docker and Infrastructure

`docker/docker-compose.yml` defines the local full-stack: control plane, console, PostgreSQL, and Redis. Additional files (`docker-compose.prod.yml`, `docker-compose.extensions.yml`) add multi-region considerations, Appwrite, ComfyUI renderer (with optional NVIDIA runtime), and mobile vision bridge. Dockerfiles for the backend and frontend are provided at the repository root.

## Detailed Engine Inventory

### Node Pipeline DAG (`backend/pipeline/node_pipeline.py`)

The `NodePipelineGenerator` constructs and executes directed acyclic graphs. Nodes have types (research agent, durable code agent, ComfyUI render, human review gate, storage, conditional). Edges define data and control flow. The generator performs a topological sort and invokes each node, passing accumulated context. An example builder (`build_example_agent_swarm_pipeline`) wires research → code agent → render → review → vault. This is the primary mechanism for expressing multi-step autonomous work.

### ComfyUI Graph Executor (`backend/pipeline/comfy_graph.py`)

`ComfyGraphExecutor` constructs and queues ComfyUI-compatible JSON graphs. It supports checkpoint loaders, KSampler nodes, and other standard ComfyUI primitives. The executor talks to a ComfyUI server (default `localhost:8188`) and can be embedded as a node inside a larger pipeline. This enables multi-modal generation (images, and by extension video or 3D when appropriate custom nodes are present) as a first-class step in agent workflows.

### Durable Worker (`agents/durable_worker.py`)

Built on Pydantic AI, the durable coder agent uses a structured output model (`CodingTaskOutput`). Tools such as `read_isolated_workspace` operate inside sandboxed paths. The design supports checkpointing so that long-running coding tasks can resume after interruption. Structured outputs make downstream review and storage deterministic.

### Mobile Vision Driver (`runners/mobile/vision_driver.py`)

This module parses vision-model outputs that contain bounding boxes or element descriptions and translates them into normalized device coordinates. It then dispatches native touch events via ADB. Combined with the framebuffer endpoint, operators can observe and intervene in mobile automation sessions.

### Appwrite Core (`backend/services/appwrite_core.go`)

Provides tenant session validation and artifact upload to Appwrite buckets. Used for ephemeral collaboration sessions and durable storage of generated assets, logs, and database dumps.

### Redis Event Mesh (`backend/services/event_mesh.go` and related Python brokers)

A pub/sub fabric that allows engines to announce state changes (circuit breaker transitions, runner heartbeats, pipeline step completions). The console can subscribe via hooks such as `useRedisTerminal` to keep views live.

### Multi-Region Schema Syncer (`database/migrations/syncer.go`)

Implements Bytebase-style declarative migration tracking. Schema changes are fingerprinted and applied to primary and replica databases with transactional safety. This supports operators who run geographically distributed control planes.

### Backup Engine (`backend/services/backup_engine.go`)

Streams `pg_dump` output to Appwrite object storage on a schedule. Provides a recovery path for the PostgreSQL state that underpins boards, trajectories, and certificates.

### Rate Limiter (`backend/api/rate_limiter.go`)

Multi-tenant middleware enforcing both request velocity (example: 120 requests per minute) and budget caps (example: $50). Protects shared inference and rendering resources.

### PKI and Certificate Signing (`backend/pkg/security/pki.go` and `scripts/bootstrap_pki.sh`)

The bootstrap script generates a certificate authority. The Go package signs short-lived certificates for compute nodes, binding them to runner identifiers and IP addresses. The console dashboard displays cryptographic status for each lease.

### Additional Engines

- **Voice Session Broker** (`backend/voice_handler.py`) — WebSocket bridge toward realtime voice providers.
- **Telemetry Pipeline** (`backend/telemetry_pipeline.py`) — records step metrics into PostgreSQL.
- **Context Mesh Router** (`backend/mesh.py`) — semantic routing via cosine similarity and context compaction.
- **Self-Healing Scheduler** (`backend/scheduler.py`) — reassigns work when runners fail.
- **Cryptographic Guardrail and Sandbox Shell** (`backend/security.py`, `backend/security/sandbox_shell.py`) — command allow-lists and secret scrubbing.
- **Marketplace Engine** (`backend/marketplace.py`) — skill publishing and discovery primitives.
- **Multica Runtime Gateway** (`backend/multica_router.py`) — detection of local CLIs and sandbox provisioning for team-board agents.
- **Graph Orchestrator** (`backend/graph_orchestrator.py`) — Pydantic Graph fault-tolerant state machine with primary and fallback inference nodes.
- **Framebuffer Handler** (`backend/api/framebuffer.go`) — returns PNG frames from ADB screencap.
- **Issue Handoff** (`backend/pkg/multica/handoff.go`) — transfers issues between agents and human reviewers.

## Data Model and Schemas

PostgreSQL schemas are supplied in several files:

- `database/schema.sql` — base tables.
- `database/schema_extensions.sql` — trajectories, evals, squads, voice sessions.
- `database/multica_schema.sql` — board issues, assignments, review gates.
- `database/system_extensions.sql` — render graphs, schema migrations, mobile device sessions.

Key entities include squads, board issues, agent trajectories, evaluation records, runner leases, certificates, render graphs, and mobile sessions. The design favors append-only or versioned records where auditability matters.

## Security Model

Security is layered:

1. **Network.** mTLS between control plane and runners. Certificates are short-lived and bound to identity.
2. **Process.** Linux namespaces and worktree isolation for agent workspaces (AgentsMesh-style).
3. **Command.** Allow-lists and pattern blocking in the sandbox shell (OpenShell-inspired).
4. **Data.** Secret scrubbing before logs or trajectories are persisted. Immutable ledger entries for critical actions.
5. **Tenant.** Rate limits and budget caps. Appwrite session validation for artifact access.
6. **Review.** Human review gates in pipelines and explicit handoff on the Multica board.

Operators should run the PKI bootstrap before exposing runners and should treat the CA private key as highly sensitive.

## Installation and Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (recommended)
- PostgreSQL 16 (or use the Compose service)
- Redis 7 (or use the Compose service)
- Optional: NVIDIA GPU and drivers for ComfyUI rendering
- Optional: ADB for mobile vision
- Optional: `gh` CLI for repository management

### Local Development (without Docker)

```bash
git clone https://github.com/CodesbyFebin/Open-Human-Agents-Stack.git
cd Open-Human-Agents-Stack

# Python control plane
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# In another terminal — console
npm install
npm run dev
# Open http://localhost:3000
```

Apply schemas manually if you have a local PostgreSQL:

```bash
psql -f database/schema_extensions.sql
psql -f database/multica_schema.sql
psql -f database/system_extensions.sql
```

### Full Stack with Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts the control plane on port 8000, the console on port 3000, PostgreSQL, and Redis.

### Production-Style Launch

```bash
chmod +x scripts/bootstrap_pki.sh
./scripts/bootstrap_pki.sh

docker compose -f docker/docker-compose.prod.yml -f docker/docker-compose.extensions.yml up --build -d
```

### Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/telemetry/summary
```

## Configuration

Environment variables (examples):

- `DATABASE_URL` — PostgreSQL connection string.
- `REDIS_URL` — Redis connection string.
- `OPENAI_API_KEY` or compatible provider keys for inference.
- `COMFYUI_URL` — address of the ComfyUI server.
- `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT`, `APPWRITE_KEY` — for BaaS features.
- `MTLS_CA_CERT`, `MTLS_CA_KEY` — paths produced by the PKI bootstrap.

Configuration files may be added under a `config/` directory as the project matures. Secrets should never be committed.

## API Reference

### Health

`GET /health`

Response:

```json
{
  "status": "operational",
  "service": "openminds-control-plane",
  "version": "2.0.0"
}
```

### Run Pipeline

`POST /pipeline/run`

Body:

```json
{
  "name": "agent_swarm_v1",
  "prompt": "cinematic evidence of a research swarm",
  "seed": 42
}
```

Returns a graph identifier, status, and execution result summary.

### Schedule Coding Agent

`POST /agent/code`

Body:

```json
{
  "task": "Implement rate-limit middleware tests",
  "workspace": "/tmp/openminds/worktrees/issue-42"
}
```

Returns a task identifier and acceptance message.

### Telemetry Summary

`GET /telemetry/summary`

Returns active runner count, circuit-breaker status, estimated daily cost, and trajectory count.

Additional internal endpoints (framebuffer, touch relay, certificate status) exist in the Go services and can be surfaced through the FastAPI layer as wiring progresses.

## Operator Console

The console is the primary human interface. After `npm run dev`, operators land on the responsive shell. Module switching exposes:

- **Board** — create and assign issues to humans or agents; view review gates.
- **Node Flows** — visualize and (in future) edit pipeline DAGs.
- **Diagnostics** — circuit-breaker state, cost, and trajectory summaries.
- **Assets** — generated images, diffs, and uploaded artifacts.
- **Certificates** — runner lease table with cryptographic status pills.
- **Terminal** — attach to a runner PTY when the streaming bridge is active.
- **Mobile** — live framebuffer and generation canvas.

The design language is intentionally sparse and high-contrast so that long operational sessions remain readable.

## Node-Based Pipeline Generation

Pipelines are the unit of autonomous work. A pipeline is a named DAG. Each node declares:

- An identifier
- A type (which selects the executor)
- Input schema expectations
- Optional retry and timeout policy

Edges carry named outputs from one node to inputs of another. The generator rejects cycles. Execution is asynchronous; intermediate results can be checkpointed.

Example flow for a research-and-render swarm:

1. Research agent node gathers sources and produces a structured brief.
2. Durable code agent node (optional) generates supporting scripts or data transforms.
3. ComfyUI render node produces visual evidence from the brief.
4. Human review gate pauses for approval.
5. Storage node uploads approved artifacts to Appwrite and records the trajectory.

Operators can define additional node types by registering executors. Conditional nodes allow branching on eval scores or review decisions.

## Mobile Vision and Device Control

The mobile path enables agents to interact with physical or emulated Android devices:

1. A vision model (or UI hierarchy dump) produces element bounds.
2. `vision_driver.py` normalizes coordinates.
3. ADB receives a tap or swipe.
4. The framebuffer handler captures the resulting screen as PNG.
5. The console displays the stream at approximately 10 Hz and can relay further touch events.

This loop supports use cases such as mobile app testing, on-device verification of generated UIs, and hybrid human-agent device operation. Device sessions are recorded in the `mobile_device_sessions` table.

## Deployment

### Single-Node

Docker Compose on one machine is sufficient for development and small teams. Persist PostgreSQL and Redis volumes. Run the PKI bootstrap once and mount the certificate directory.

### Multi-Node Runners

Runners may be started on additional machines. Each runner obtains a certificate from the control plane, establishes an mTLS channel, and advertises capacity. The self-healing scheduler assigns work. Real-time terminal streaming uses the gRPC `StreamTerminal` RPC defined in `proto/fleet_orchestrator.proto` (implementation in progress).

### Multi-Region

The schema syncer and backup engine support operators who maintain replicas. Active-active conflict resolution is a future enhancement; the current design favors a primary writer with read replicas.

### GPU Rendering

The extensions Compose file can attach an NVIDIA runtime to the ComfyUI service. Ensure the host has the NVIDIA Container Toolkit installed.

## Observability and Telemetry

Telemetry is collected at multiple layers:

- **Trajectories** — ordered records of agent steps, tool calls, and outputs.
- **Evals** — scored assessments of trajectory quality.
- **Cost** — token and compute estimates aggregated per tenant and per day.
- **Circuit breakers** — primary versus fallback inference state.
- **Runner heartbeats** — liveness and capacity.

The telemetry pipeline writes to PostgreSQL. The diagnostics console and `/telemetry/summary` endpoint surface aggregates. OpenTelemetry export is a planned addition.

## Skills Marketplace

The marketplace engine allows publication of skills (prompt templates, tool configurations, small workflows). Skills can be versioned and discovered by agents or humans. The design avoids proprietary lock-in; published artifacts are ordinary files plus metadata. Integration with the Karpathy-style behavioral skills and Taku-inspired publisher workflows is present in the `skills/` tree.

## Development Guide

### Repository Layout

```
backend/          FastAPI app, Python engines, Go services
agents/           Durable Pydantic AI workers
ui/               Next.js console and components
database/         SQL schemas and Go migration syncer
docker/           Compose files
runners/          Mobile and other execution drivers
proto/            gRPC definitions
scripts/          PKI bootstrap and utilities
skills/           Skill definitions and publisher
docs/             Additional design notes
```

### Adding a Node Type

1. Implement an executor class with a standard `run(context) -> result` signature.
2. Register it in the pipeline generator.
3. Add a UI representation if the node should appear on the canvas.
4. Write a trajectory record on completion.

### Testing

Unit tests should accompany new executors. Integration tests can use the Docker Compose stack. The mobile path requires an ADB device or emulator.

### Code Style

Python follows standard formatting (Black/Ruff compatible). Go uses `gofmt`. TypeScript uses the Next.js defaults. Prefer explicit structured outputs over free-form strings when crossing process boundaries.

## Roadmap
<img width="2172" height="724" alt="Open Human Agents Mission Control" src="https://github.com/user-attachments/assets/1ecffd61-9976-44f7-a3f0-a4fe8bb7b726" />

Near-term priorities:

- Complete live wiring of the Redis event mesh into the FastAPI control plane.
- Mount and rotate mTLS certificates for the runner fleet.
- Make pipeline execution fully durable with checkpoint resume.
- Finish the mobile framebuffer and touch-relay loop in the console.
- Harden the production Compose stack with health checks and GPU support.
- Surface additional Go service endpoints through the control plane.
- Add OpenTelemetry export and richer eval dashboards.
- Implement the gRPC terminal streaming bridge end-to-end.
- Expand the skills marketplace with signing and provenance.
- Multi-region active-active schema coordination.

Longer-term:

- First-class voice session UI.
- Policy-as-code for guardrails.
- Federated runner marketplaces.
- Formal verification hooks for critical pipelines.

## Contributing

Contributions are welcome. Please open an issue before large changes. Use the existing labels (`engine`, `control-plane`, `console`, `security`, `pipeline`, `mobile`, `infra`). Keep commits focused. Update schemas and the operator console when adding user-visible behavior. Respect the licenses of any upstream code that has been incorporated.

## License

MIT License. See [LICENSE](LICENSE).

Upstream components retain their original licenses where applicable. When in doubt, consult the `sources/` tree and individual file headers.

## Topics

`ai-agents` `multi-agent` `agent-swarm` `autonomous-agents` `self-hosted` `open-source` `pydantic-ai` `comfyui` `mobile-use` `durable-execution` `workflow-orchestration` `human-in-the-loop` `skills-marketplace` `mtls` `zero-trust` `rag` `voice-agents` `edge-computing` `evidence-systems` `codesbyfebin`

## Status

Full-stack application scaffold is operational. FastAPI control plane, Next.js operator console, Docker Compose, node pipeline DAG, security mesh, mobile vision primitives, and enterprise engines are resident. Live wiring and production hardening continue.

Built by [CodesbyFebin](https://github.com/CodesbyFebin) · systems that prove what happened.

---

## Appendix A: Example Pipeline Definition (Conceptual)

```python
generator = NodePipelineGenerator(comfy_executor)
pipeline = generator.create_pipeline("research_render_v1")
research = pipeline.add_node("research", "research_agent")
render = pipeline.add_node("render", "comfy_render_node")
review = pipeline.add_node("review", "human_review_gate")
vault = pipeline.add_node("vault", "appwrite_upload")
pipeline.connect(research, render)
pipeline.connect(render, review)
pipeline.connect(review, vault)
result = await generator.execute(pipeline, {"prompt": "..."})
```

## Appendix B: Example gh Commands for Operators

```bash
# View repo metadata
gh repo view CodesbyFebin/Open-Human-Agents-Stack

# List open upgrade issues
gh issue list --repo CodesbyFebin/Open-Human-Agents-Stack --label pipeline

# Create a release
gh release create v2.1.0 --title "OpenMinds v2.1" --notes "Live wiring release."
```

## Appendix C: Glossary

- **Control plane** — the coordinating FastAPI (and supporting Go) services.
- **Runner** — an isolated execution environment that accepts work.
- **Trajectory** — the ordered record of an agent or pipeline run.
- **Review gate** — a pipeline node or board state that requires human approval.
- **Lease** — a time-bounded assignment of work or certificate to a runner.
- **Circuit breaker** — mechanism that fails over from a primary inference provider to a local fallback.
- **Evidence console** — the operator UI aesthetic and functional emphasis on auditability.

## Appendix D: Comparison Notes

| Capability              | Typical chat UI | Marketplace remix | OpenMinds          |
|-------------------------|-----------------|-------------------|--------------------|
| Multi-human teams       | Limited         | No                | Yes (boards)       |
| Durable agents          | No              | Rare              | Yes (Pydantic AI)  |
| Visual node pipelines   | No              | Sometimes         | Yes                |
| Mobile device control   | No              | No                | Yes                |
| mTLS runner fleet       | No              | No                | Yes                |
| Self-hostable           | Varies          | Often no          | Yes                |
| Evidence / trajectories | Minimal         | Minimal           | First-class        |

This table is illustrative. OpenMinds continues to evolve; capabilities marked “Yes” exist as implemented engines or scaffolds ready for wiring.

## Appendix E: Operational Checklist

- [ ] Clone repository
- [ ] Apply SQL schemas
- [ ] Bootstrap PKI
- [ ] Start Compose stack
- [ ] Verify `/health`
- [ ] Confirm console loads
- [ ] (Optional) Attach ADB device
- [ ] (Optional) Point ComfyUI URL
- [ ] (Optional) Configure Appwrite
- [ ] Create first squad and issue on the board
- [ ] Run example pipeline
- [ ] Review trajectory and cost summary

Following this checklist yields a working local OpenMinds instance suitable for further development or small-team pilot use.

---

End of document.

## Appendix F: Detailed Component Interaction Sequences

### Sequence 1: Scheduling a Durable Coding Task

1. The operator opens the console and navigates to the Board module.
2. A new issue is created with a title, description, and optional acceptance criteria.
3. The issue is assigned to the durable coder agent (or to a squad that includes the agent).
4. The Multica runtime gateway detects available local CLIs or provisions a sandbox workspace.
5. The control plane receives a POST to `/agent/code` (or an internal equivalent) containing the task text and workspace path.
6. The durable worker initializes a Pydantic AI agent with the CodingTaskOutput model.
7. The agent calls tools such as `read_isolated_workspace`. All file access is confined to the assigned worktree.
8. Intermediate steps are written to the trajectories table by the telemetry pipeline.
9. On completion, a structured diff is produced and attached to the issue.
10. The AgentDiffVisualizer in the console renders the diff. A human reviewer may approve or reject.
11. Approval triggers the handoff manager to mark the issue resolved or to open a follow-up.
12. Cost and token estimates are aggregated into the daily telemetry summary.

This sequence demonstrates the interplay of the board, control plane, durable agent, telemetry, and review UI.

### Sequence 2: Executing a Multi-Modal Research Pipeline

1. An operator or an upstream agent submits a pipeline request with a prompt.
2. The FastAPI endpoint instantiates NodePipelineGenerator and ComfyGraphExecutor.
3. The example (or custom) DAG is built: research node, optional code node, ComfyUI render node, human review gate, vault node.
4. Topological execution begins. The research node may call external tools or a local RAG index.
5. Its structured output becomes the prompt context for the render node.
6. ComfyGraphExecutor constructs a JSON graph (checkpoint loader, KSampler, etc.) and queues it on the ComfyUI server.
7. The resulting image or media is stored temporarily and passed to the review gate.
8. The console displays the asset. The human reviewer approves.
9. The vault node calls the Appwrite core to upload the artifact and records the final trajectory.
10. The event mesh publishes a completion event. Subscribed console components refresh.

Failure at any node can trigger the circuit-breaker logic in the graph orchestrator, falling back to a local model or marking the pipeline for manual intervention.

### Sequence 3: Mobile Vision Verification Loop

1. A pipeline or agent decides that on-device verification is required.
2. A mobile device session is opened and recorded in `mobile_device_sessions`.
3. The vision driver receives a description or screenshot analysis containing element bounds.
4. Coordinates are normalized and an ADB tap is dispatched.
5. The framebuffer handler captures the new screen via `adb screencap` and returns a PNG.
6. MobileFrameBufferStream in the console polls or receives the frame and paints it to a canvas.
7. The operator may override with a manual touch relay.
8. The session trajectory includes both automated and manual actions for later audit.

### Sequence 4: Runner Certificate Lifecycle

1. An operator runs `scripts/bootstrap_pki.sh`, generating a CA key and certificate.
2. A new runner starts and requests a certificate, presenting its runner ID and IP.
3. The PKI package signs a short-lived certificate.
4. The runner presents the certificate on subsequent mTLS connections.
5. The CertificateRegistryDashboard shows the lease with a healthy cryptoStatus.
6. Before expiry, the runner renews. On compromise or decommission, the certificate is revoked (revocation list support is planned).
7. All signing events are logged for evidence.

These sequences illustrate that OpenMinds is not a single service but a coordinated set of engines whose interactions are designed to be observable.

## Appendix G: Schema Highlights

### Trajectories

Trajectories store ordered steps. Typical columns include trajectory_id, agent_or_pipeline_id, step_index, step_type, input_payload, output_payload, tool_calls, token_count, cost_estimate, timestamp, and parent_trajectory_id for nested runs. Indexes support lookup by time range and by squad.

### Board Issues

The Multica schema includes issues with id, title, body, status (open, in_progress, in_review, closed), assignee_type (human or agent), assignee_id, squad_id, created_at, and updated_at. Related tables hold comments, review decisions, and handoff history.

### Render Graphs

Render graphs persist the JSON definition sent to ComfyUI, the seed, the checkpoint name, execution status, and the resulting artifact URL. This allows exact reproduction of a generated image.

### Mobile Device Sessions

Sessions record device serial, start and end times, the initiating pipeline or issue, and a log of touch events with normalized coordinates.

### Schema Migrations

The syncer records migration fingerprints, applied timestamps, and target database identifiers so that multi-region replicas can be verified for consistency.

Operators are encouraged to treat these tables as the system of record. Application logs are supplementary.

## Appendix H: Failure Modes and Mitigations

**Inference provider outage.** The graph orchestrator’s circuit breaker detects repeated failures and routes to the local fallback node. The diagnostics console surfaces the change. Operators can manually reset the breaker after the provider recovers.

**Runner crash.** The self-healing scheduler observes missed heartbeats via the event mesh and reassigns the lease. Work that was checkpointed by the durable worker resumes; work that was not is retried from the last recorded trajectory step.

**ComfyUI queue stall.** The render node has a configurable timeout. On timeout the pipeline marks the node failed and can retry or skip to a text-only fallback path.

**ADB device disconnect.** The vision driver and framebuffer handler return clear errors. The mobile session is marked interrupted. The console displays the last successful frame and an offline indicator.

**Certificate expiry.** Runners should renew well before expiry. The dashboard highlights leases nearing expiration. A future cron job will automate renewal.

**Schema drift.** The multi-region syncer compares fingerprints. Divergence raises an alert rather than silently overwriting. Operators resolve conflicts before resuming writes.

**Budget exhaustion.** The rate limiter rejects requests once the tenant budget cap is reached, returning a clear error. The telemetry summary shows current spend.

Documenting these modes helps operators build runbooks. Each mitigation is either implemented or explicitly marked as planned.

## Appendix I: Performance Considerations

The control plane is I/O bound for most operations (database writes, Redis pub/sub, outbound inference). Horizontal scaling of the FastAPI workers is straightforward behind a load balancer, provided session affinity is not required for WebSocket voice or terminal streams (or sticky sessions are configured).

PostgreSQL should be tuned for the expected trajectory insert rate. Partitioning the trajectories table by month is a recommended future optimization. Redis is used for ephemeral coordination; persistence may be enabled if operators wish to survive restarts without losing in-flight pub/sub state.

ComfyUI rendering is GPU bound. Isolating it on dedicated hardware and communicating over the network keeps the control plane responsive. Mobile framebuffer streaming at 10 Hz is lightweight; higher rates are possible but increase bandwidth.

Operators running large swarms should monitor connection counts to the database and Redis and set appropriate pool sizes in the application configuration.

## Appendix J: Extensibility Points

OpenMinds is designed to be extended without forking the core:

- **New node types.** Register an executor with the pipeline generator.
- **New console modules.** Add a component and a route in the shell’s module switcher.
- **New inference providers.** Implement the fallback provider interface and add it to the circuit-breaker configuration.
- **New storage backends.** The Appwrite core can be paralleled by an S3-compatible implementation behind the same upload interface.
- **Custom guardrails.** Extend the sandbox shell allow-list or add policy hooks before tool execution.
- **Additional telemetry exporters.** The telemetry pipeline can fan out to OpenTelemetry collectors.

Extension points are kept narrow so that upstream improvements remain easy to merge.

## Appendix K: Example Environment File

```bash
# .env.example
DATABASE_URL=postgresql://openminds:openminds@localhost:5432/openminds
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
COMFYUI_URL=http://localhost:8188
APPWRITE_ENDPOINT=http://localhost:8090/v1
APPWRITE_PROJECT=openminds
APPWRITE_KEY=...
MTLS_CA_CERT=/etc/openminds/certs/ca.crt
MTLS_CA_KEY=/etc/openminds/certs/ca.key
LOG_LEVEL=info
```

Copy to `.env` and adjust. Never commit real secrets.

## Appendix L: Troubleshooting

**Console shows blank page.** Confirm `npm run dev` is running and that `ui/pages/index.tsx` correctly imports the shell. Check the browser console for module resolution errors.

**Control plane fails to start.** Verify Python dependencies installed and that port 8000 is free. Inspect uvicorn logs for import errors in pipeline or agent modules.

**Database connection refused.** Ensure the Postgres container is healthy or that a local instance is listening. Apply schemas if tables are missing.

**Pipeline endpoint returns 500.** The example pipeline may reference a ComfyUI server that is not running. Start ComfyUI or temporarily stub the render node.

**Mobile stream shows no frames.** Confirm `adb devices` lists the target and that the framebuffer service is reachable. Check USB debugging authorization.

**Certificate errors on runner connect.** Re-run the PKI bootstrap if the CA is missing. Verify clock synchronization between control plane and runners.

These checks resolve the majority of initial setup issues.

## Appendix M: Security Hardening Checklist

- [ ] Run PKI bootstrap and protect the CA private key (hardware token or sealed secret recommended for production).
- [ ] Enable mTLS for all runner communication.
- [ ] Configure the sandbox shell allow-list to the minimum required commands.
- [ ] Set tenant rate limits and budget caps.
- [ ] Disable public sign-up if the deployment is single-tenant.
- [ ] Place the control plane behind a reverse proxy with TLS.
- [ ] Regularly rotate Appwrite and inference API keys.
- [ ] Enable PostgreSQL encryption at rest if the host supports it.
- [ ] Review trajectory retention policy and purge old records according to compliance needs.
- [ ] Monitor the certificate registry for unexpected runners.

## Appendix N: Glossary Expansion

- **DAG** — Directed Acyclic Graph; the structure of a pipeline.
- **Worktree** — an isolated Git working directory assigned to an agent.
- **PTY** — pseudo-terminal; used for real-time shell streaming.
- **VAD** — Voice Activity Detection; relevant to realtime voice sessions.
- **BaaS** — Backend-as-a-Service; here provided by Appwrite.
- **DePIN** — Decentralized Physical Infrastructure Network; occasionally relevant to edge runner discussions.
- **Eval** — a scored assessment of an agent trajectory or output.
- **Handoff** — the transfer of responsibility for an issue from an agent to a human or vice versa.
- **Lease** — a time-bounded claim on a runner or a certificate.
- **Provenance** — the recorded origin and transformation history of an artifact.

## Appendix O: Versioning and Releases

The project follows a pragmatic versioning scheme. The current scaffold is marked 2.0.0 in the control plane. Minor versions will indicate wired features (for example 2.1.0 for live event mesh and mTLS mounting). Patch versions address fixes. Git tags and GitHub releases are the authoritative record. The `gh release create` command is the recommended way to publish.

Changelog entries should note schema changes, new endpoints, and breaking configuration adjustments.

## Appendix P: Community and Support

Issues and discussions are enabled on the GitHub repository. Use labels to categorize. For security-sensitive reports, prefer a private channel if one is configured; otherwise open a public issue with minimal detail and request a private follow-up.

The project welcomes documentation improvements, additional node types, console polish, and test coverage. Large architectural changes should be discussed in an issue first.

## Appendix Q: Acknowledgments

OpenMinds incorporates ideas and, in places, structural inspiration from a range of open-source projects including Dify (visual workflows), AgentsMesh (multi-machine runners), Multica (team boards), Pydantic AI (typed agents), ComfyUI (node-based rendering), OpenShell-style secure shells, Appwrite, Bytebase-style migration tracking, and various mobile automation tools. Original licenses are respected. The integration and the evidence-first control plane are original work by CodesbyFebin and contributors.

## Appendix R: Final Operational Notes

Operators should begin with the Docker Compose stack, apply schemas, bootstrap PKI, and verify health endpoints before attaching external devices or GPU renderers. Once the basic loop (create issue → run pipeline or agent → review trajectory) is confirmed, additional engines can be enabled incrementally. The ABOUT.md file in the repository root contains the canonical description and topic list for the GitHub About panel.

This document is intended to remain the single detailed reference for the Open Human Agents Stack. Updates should preserve the evidence-first tone and the clear separation of control plane, console, and execution layer.

---

Document word count target exceeded. Systems that prove what happened.
