import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_swagger_ui_loads():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/docs")
    assert response.status_code == 200

# Further testing requires an active database setup per session.
# Recommendation: use a fixture overriding `get_db` to yield
# an async session on an ephemeral PostgreSQL database.
