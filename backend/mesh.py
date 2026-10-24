# backend/mesh.py
# Context & routing mesh for multi-agent coordination

import json
import numpy as np
from typing import List, Dict, Any

class ContextMeshRouter:
    def __init__(self, db_connection):
        self.db = db_connection

    def calculate_cosine_similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        a = np.array(vector_a)
        b = np.array(vector_b)
        if not a.any() or not b.any():
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def route_by_semantic_density(self, payload_embedding: List[float], squad_id: str) -> Dict[str, Any]:
        cursor = self.db.cursor()
        cursor.execute("SELECT id, node_name, semantic_signature FROM agent_nodes WHERE squad_id = %s AND is_active = TRUE", (squad_id,))
        nodes = cursor.fetchall()
        
        highest_score = -1.0
        selected_node = None
        
        for node_id, name, signature in nodes:
            if not signature:
                continue
            sig_vector = json.loads(signature)
            score = self.calculate_cosine_similarity(payload_embedding, sig_vector)
            if score > highest_score:
                highest_score = score
                selected_node = {"id": node_id, "name": name, "density_score": score}
                
        return selected_node or {"error": "No matching computational targets resolved."}

    def compact_context_window(self, history_buffer: List[Dict[str, Any]], retention_threshold: float) -> List[Dict[str, Any]]:
        compacted = []
        for element in history_buffer:
            if element.get("relevance_score", 1.0) >= retention_threshold or element.get("role") == "system":
                compacted.append(element)
        return compacted

    def broadcast_mesh_event(self, topology_id: str, event_data: Dict[str, Any]) -> bool:
        if not topology_id or not event_data:
            return False
        return True
