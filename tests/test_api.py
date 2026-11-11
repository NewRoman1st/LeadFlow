import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Use an isolated database so tests never touch a real local database.
TEST_DB = tempfile.NamedTemporaryFile(delete=False)
TEST_DB.close()
os.environ["DATABASE_PATH"] = TEST_DB.name

from app.main import app  # noqa: E402

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_list_update_and_report(client):
    created = client.post(
        "/leads",
        json={
            "name": "Иван Петров",
            "phone": "+79990000000",
            "service": "Ремонт ноутбука",
            "message": "Не включается устройство",
        },
    )
    assert created.status_code == 201
    lead = created.json()
    assert lead["status"] == "new"

    listed = client.get("/leads?status=new")
    assert listed.status_code == 200
    assert any(item["id"] == lead["id"] for item in listed.json())

    updated = client.patch(
        f"/leads/{lead['id']}/status",
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    report = client.get("/reports/summary")
    assert report.status_code == 200
    assert report.json()["total"] == 1
    assert report.json()["by_status"]["in_progress"] == 1


def test_missing_lead_returns_404(client):
    response = client.get("/leads/999999")
    assert response.status_code == 404
