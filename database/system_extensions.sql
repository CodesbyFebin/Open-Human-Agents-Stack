-- database/system_extensions.sql
-- Render graphs, schema migrations, mobile sessions, fallback routes

CREATE TABLE IF NOT EXISTS render_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    graph_json JSONB NOT NULL,
    execution_status VARCHAR(50) DEFAULT 'QUEUED',
    output_artifacts TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_alias VARCHAR(100) NOT NULL,
    version_tag VARCHAR(50) NOT NULL,
    migration_payload TEXT NOT NULL,
    execution_fingerprint VARCHAR(64) NOT NULL,
    applied_by_entity_id UUID NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mobile_device_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    device_os VARCHAR(50) NOT NULL,
    current_activity_view TEXT,
    last_screen_bounds_json JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fallback_inference_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    rate_limit_reset TIMESTAMP WITH TIME ZONE,
    is_operational BOOLEAN DEFAULT TRUE,
    consecutive_failures INT DEFAULT 0
);
