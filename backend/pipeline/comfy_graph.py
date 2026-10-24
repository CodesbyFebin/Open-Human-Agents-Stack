# backend/pipeline/comfy_graph.py
# ComfyUI node graph executor for multi-modal rendering

import json
import urllib.request
from typing import Dict, Any

class ComfyGraphExecutor:
    def __init__(self, server_address: str):
        self.server_address = server_address

    def queue_node_graph(self, prompt_graph: Dict[str, Any], client_id: str) -> str:
        payload = {"prompt": prompt_graph, "client_id": client_id}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("prompt_id", "")
        except Exception as e:
            raise RuntimeError(f"Multi-modal generation node tracking loop failed: {e}")

    def evaluate_generation_primitives(self, text_prompt: str, seed: int = 42) -> Dict[str, Any]:
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8, "denoise": 1.0, "sampler_name": "euler",
                    "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["5", 0], "seed": seed, "steps": 20
                }
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "flux1-dev.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 1024, "width": 1024}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": text_prompt}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "blurry, low quality, artifacting"}}
        }
