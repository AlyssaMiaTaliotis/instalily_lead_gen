import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
pytest_plugins = ("pytest_asyncio",)

from backend.api.main import app, leads_storage, events_storage, companies_storage, outreach_storage

def test_pytest_collection_works():
    assert True

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_clear_all_data():
    # Put mock data
    leads_storage.append({"id": "mock"})
    events_storage.append({"name": "mock_event"})
    companies_storage.append({"name": "mock_company"})
    outreach_storage.append({"lead_id": "mock"})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/leads/clear")
        assert response.status_code == 200
        assert response.json()["message"] == "All data cleared successfully"
        assert leads_storage == []
        assert events_storage == []
        assert companies_storage == []
        assert outreach_storage == []

@pytest.mark.asyncio
async def test_task_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/task-status")
        assert res.status_code == 200
        assert "status" in res.json()

@pytest.mark.asyncio
async def test_export_leads_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/export/leads")
        body = res.json()
        assert res.status_code == 200
        assert body["count"] == 0
        assert isinstance(body["data"], list)

@pytest.mark.asyncio
async def test_generate_leads_trigger():
    payload = {
        "target_industries": ["signage"],
        "max_leads": 5,
        "min_company_size": "medium",
        "include_outreach": False
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/generate-leads", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "initiated"