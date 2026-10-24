# backend/telemetry_pipeline.py
# Real-time telemetry and cost recording

import time
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import Json

class TelemetryPipeline:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def record_step_metrics(self, run_id: str, node_id: str, step: int, metrics: Dict[str, Any]):
        """Commits performance data entries into persistent telemetry tables."""
        query = """
            INSERT INTO agent_trajectories (
                run_id, step_number, node_id, prompt_tokens, 
                completion_tokens, cost_usd, tool_calls, 
                model_response, latency_ms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        
        conn = psycopg2.connect(self.dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    run_id,
                    step,
                    node_id,
                    metrics.get("prompt_tokens", 0),
                    metrics.get("completion_tokens", 0),
                    metrics.get("cost_usd", 0.0),
                    Json(metrics.get("tool_calls", [])),
                    metrics.get("model_response", ""),
                    metrics.get("latency_ms", 0)
                ))
                trajectory_id = cur.fetchone()[0]
                conn.commit()
                return trajectory_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
