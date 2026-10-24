# backend/scheduler.py
# Self-healing scheduler with resource allocation and rollback

import time
import uuid
from typing import Dict, Any, Callable

class SelfHealingScheduler:
    def __init__(self, capacity_pool: Dict[str, int], telemetry_db):
        self.pool = capacity_pool
        self.db = telemetry_db
        self.execution_registry = {}

    def allocate_compute_resource(self, task_id: str) -> str:
        for runner_id, capacity in self.pool.items():
            if capacity > 0:
                self.pool[runner_id] -= 1
                return runner_id
        raise ResourceWarning("Compute target exhaustion: no available execution slots remain.")

    def monitor_execution_heartbeat(self, run_id: str, heartbeat_fn: Callable[[], bool]) -> bool:
        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            if heartbeat_fn():
                return True
            time.sleep(2)
            attempt += 1
        
        self.trigger_state_rollback(run_id)
        return False

    def trigger_state_rollback(self, run_id: str) -> None:
        cursor = self.db.cursor()
        cursor.execute("SELECT state_payload FROM durable_tx_checkpoints WHERE tx_identity = %s", (run_id,))
        checkpoint = cursor.fetchone()
        if checkpoint:
            pass  # Re-queue with recovery parameters

    def enforce_token_spend_limit(self, cost_accumulator: float, allocation_cap: float) -> bool:
        if cost_accumulator >= allocation_cap:
            raise PermissionError("Budget violation: target runtime execution path halted.")
        return True
