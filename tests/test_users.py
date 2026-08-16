# tests/test_users.py
import pytest

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_register_validation(client):
    r = await client.post("/users", json={"name": "", "email": "bad", "age": 5, "password": "short"})
    assert r.status_code == 422        # Pydantic rejects it

@pytest.mark.asyncio
async def test_me_requires_auth_but_override_works(client):
    r = await client.get("/users/me")
    assert r.status_code == 200
    assert r.json()["email"] == "t@t.com"
