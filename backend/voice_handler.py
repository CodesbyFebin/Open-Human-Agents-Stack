# backend/voice_handler.py
# Bidirectional real-time voice session broker

import json
import asyncio
import websockets
from typing import Dict, Any

class VoiceSessionBroker:
    def __init__(self, model_endpoint: str, api_key: str):
        self.model_endpoint = model_endpoint
        self.api_key = api_key

    async def bridge_audio_stream(self, client_ws: websockets.WebSocketServerProtocol):
        """Maintains ultra-low latency bridging for interactive voice loops."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        async with websockets.connect(self.model_endpoint, extra_headers=headers) as server_ws:
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": "You are an automated code engineer workspace companion. Respond precisely.",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {"type": "server_vad"}
                }
            }
            await server_ws.send(json.dumps(session_update))

            async def client_to_model():
                async for message in client_ws:
                    data = json.loads(message)
                    if data.get("type") == "input_audio_buffer.append":
                        await server_ws.send(json.dumps(data))

            async def model_to_client():
                async for message in server_ws:
                    data = json.loads(message)
                    if data.get("type") in ["reply.audio.delta", "reply.text.delta"]:
                        await client_ws.send(json.dumps(data))

            await asyncio.gather(client_to_model(), model_to_client())
