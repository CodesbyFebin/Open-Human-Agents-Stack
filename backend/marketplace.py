# backend/marketplace.py
# Skills marketplace and fractional billing

import json
from typing import Dict, Any, List

class MarketplaceEngine:
    def __init__(self, registry_db):
        self.db = registry_db

    def compute_fractional_billing(self, execution_metrics: Dict[str, Any], rate_card: Dict[str, float]) -> float:
        prompt_cost = execution_metrics.get("prompt_tokens", 0) * rate_card.get("prompt_rate", 0.0)
        completion_cost = execution_metrics.get("completion_tokens", 0) * rate_card.get("completion_rate", 0.0)
        compute_ms_cost = execution_metrics.get("duration_ms", 0) * rate_card.get("compute_ms_rate", 0.0)
        
        return float(prompt_cost + completion_cost + compute_ms_cost)

    def bundle_skill_package(self, manifest_data: Dict[str, Any], runtime_code: str) -> str:
        bundle = {
            "specification_version": "OM-2026-V1",
            "manifest": manifest_data,
            "executable_payload": runtime_code
        }
        return json.dumps(bundle, sort_keys=True)

    def rank_agent_efficiency(self, historical_runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ranked_nodes = []
        for run in historical_runs:
            success_weight = 1.0 if run.get("is_passing", False) else 0.0
            cost = run.get("cost_usd", 1.0)
            efficiency_score = success_weight / (cost if cost > 0 else 1.0)
            ranked_nodes.append({"node_id": run.get("node_id"), "efficiency_score": efficiency_score})
            
        return sorted(ranked_nodes, key=lambda x: x["efficiency_score"], reverse=True)
