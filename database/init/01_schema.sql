-- OpenMinds v1.0 — Base schema
-- Applied automatically by Postgres initdb

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Users & Teams ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator' CHECK (role IN ('operator','reviewer','admin','agent')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS squads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS squad_members (
    squad_id UUID REFERENCES squads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (squad_id, user_id)
);

-- ─── Board Issues (Human + Agent) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','in_progress','in_review','closed','blocked')),
    assignee_type TEXT NOT NULL CHECK (assignee_type IN ('human','agent')),
    assignee_id UUID,
    squad_id UUID REFERENCES squads(id),
    priority INT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_assignee ON issues(assignee_type, assignee_id);
CREATE INDEX IF NOT EXISTS idx_issues_squad ON issues(squad_id);

CREATE TABLE IF NOT EXISTS issue_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id),
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS review_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id),
    decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','changes_requested')),
    comment TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── Durable Jobs (Claim, Retry, Cancel) ───────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','claimed','running','completed','failed','cancelled','retrying')),
    claimed_by TEXT,
    claimed_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    error TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_retry ON jobs(next_retry_at) WHERE status = 'retrying';
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs(idempotency_key);

-- ─── Checkpoints (Durable Execution) ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT NOT NULL,
    step_index INT NOT NULL,
    step_name TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (run_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_run ON checkpoints(run_id, step_index);

-- ─── MCP Tool Approvals (Server-Side, Durable) ─────────────────────────────

CREATE TABLE IF NOT EXISTS tool_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name TEXT NOT NULL,
    approved_by UUID NOT NULL REFERENCES users(id),
    scope TEXT NOT NULL DEFAULT '*',
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_approvals_name ON tool_approvals(tool_name, is_active);

-- ─── Trajectories (Evidence) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS trajectories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT NOT NULL,
    agent_or_pipeline TEXT NOT NULL,
    step_index INT NOT NULL,
    step_type TEXT NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    tool_calls JSONB DEFAULT '[]',
    token_count INT DEFAULT 0,
    cost_estimate NUMERIC(10,6) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'completed',
    error TEXT,
    parent_trajectory_id UUID REFERENCES trajectories(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_traj_run ON trajectories(run_id, step_index);
CREATE INDEX IF NOT EXISTS idx_traj_time ON trajectories(created_at);
CREATE INDEX IF NOT EXISTS idx_traj_agent ON trajectories(agent_or_pipeline);

-- ─── Runner Fleet ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS runners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    runner_id TEXT UNIQUE NOT NULL,
    ip TEXT,
    capacity INT NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','idle','busy','decommissioned')),
    cert_fingerprint TEXT,
    last_heartbeat TIMESTAMPTZ,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_runners_status ON runners(status);

-- ─── Mobile Device Sessions ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mobile_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_serial TEXT NOT NULL,
    initiated_by UUID REFERENCES users(id),
    issue_id UUID REFERENCES issues(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','interrupted','completed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS mobile_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES mobile_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    x_norm NUMERIC(5,4),
    y_norm NUMERIC(5,4),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── Pipeline Definitions ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    definition JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
