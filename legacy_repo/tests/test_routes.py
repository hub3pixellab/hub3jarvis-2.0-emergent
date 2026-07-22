"""Testes unitarios das rotas principais do backend JARVIS v4.2"""
import pytest
from httpx import AsyncClient, ASGITransport
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from main import app

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "sistema" in data
    assert data["sistema"] == "JARVIS"

@pytest.mark.asyncio
async def test_services_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/services/status")
    assert r.status_code == 200
    assert "servicos" in r.json()

@pytest.mark.asyncio
async def test_vault_stats_sem_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/vault/stats")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_vault_stats_com_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/vault/stats", headers={"Authorization": "Bearer test"})
    assert r.status_code in (200, 404)

@pytest.mark.asyncio
async def test_ollama_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/ollama/models")
    assert r.status_code in (200, 500)

@pytest.mark.asyncio
async def test_github_repos():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/github/repos")
    assert r.status_code in (200, 500)

@pytest.mark.asyncio
async def test_ai_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/ai/models")
    assert r.status_code == 200
    assert "modelos" in r.json()

@pytest.mark.asyncio
async def test_skills_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/skills")
    assert r.status_code == 200
