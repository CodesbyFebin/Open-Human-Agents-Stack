# backend/inference/fallback_provider.py
# Zero-cost resilient inference fallback broker

import requests
from typing import List, Dict

class ResilientInferenceBroker:
    def __init__(self, high_availability_endpoints: List[str]):
        self.endpoints = high_availability_endpoints

    def execute_completion_fallback_loop(self, message_payload: List[Dict[str, str]], fallback_model: str) -> str:
        for endpoint in self.endpoints:
            try:
                response = requests.post(
                    f"{endpoint}/v1/chat/completions",
                    json={
                        "model": fallback_model,
                        "messages": message_payload,
                        "temperature": 0.2,
                        "max_tokens": 4096
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
            except requests.RequestException:
                continue
        raise ConnectionError("Global compute degradation: every registered inference network failed.")
