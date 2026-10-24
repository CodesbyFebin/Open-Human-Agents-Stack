-- database/schema_extensions.sql
-- Observability, durable execution, voice sessions for OpenMinds

-- 1. Observability and Trajectory Tracking
CREATE TABLE IF NOT EXISTS agent_trajectories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0.000000,
    tool_calls JSONB DEFAULT '[]'::jsonb,
    model_response TEXT,
    latency_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_evals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trajectory_id UUID REFERENCES agent_trajectories(id) ON DELETE CASCADE,
    evaluator_name VARCHAR(100) NOT NULL,
    score NUMERIC(3, 2) CHECK (score >= 0.0 AND score <= 1.0),
    rationale TEXT,
    is_passing BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Durable Execution and Checkpointing
CREATE TABLE IF NOT EXISTS workflow_step_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
    inputs JSONB DEFAULT '{}'::jsonb,
    outputs JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Voice Sessions Metadata
CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_status VARCHAR(50) DEFAULT 'INITIALIZING', -- 'ACTIVE', 'ENDED'
    provider VARCHAR(100) NOT NULL, -- 'openai-realtime', 'gemini-live'
    audio_duration_seconds INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
