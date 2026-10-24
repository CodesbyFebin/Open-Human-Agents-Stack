import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/health")
        assert r.status_code == 200
        assert r.json()["service"] == "openminds-control-plane"

@pytest.mark.asyncio
async def test_pipeline_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/pipeline/run", json={"name": "t", "prompt": "hi"})
        assert r.status_code == 401
