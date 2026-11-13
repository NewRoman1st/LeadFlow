import pytest
from fastapi.testclient import TestClient

from app import database, main
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Give every test its own SQLite database."""
    db_path = tmp_path / "test_leadflow.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(db_path))

    with TestClient(app) as test_client:
        yield test_client


def create_lead(client, name="Иван Петров", phone="+79990000000"):
    return client.post(
        "/leads",
        json={
            "name": name,
            "phone": phone,
            "service": "Ремонт ноутбука",
            "message": "Не включается устройство",
        },
    )


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "LeadFlow"}


def test_create_get_update_and_report(client, monkeypatch):
    notifications = []

    async def fake_notify(lead):
        notifications.append(lead["id"])
        return False

    monkeypatch.setattr(main, "notify_admin_about_lead", fake_notify)

    created = create_lead(client)
    assert created.status_code == 201
    lead = created.json()
    assert lead["status"] == "new"
    assert lead["name"] == "Иван Петров"
    assert notifications == [lead["id"]]

    fetched = client.get(f"/leads/{lead['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == lead["id"]

    updated = client.patch(
        f"/leads/{lead['id']}/status",
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    report = client.get("/reports/summary")
    assert report.status_code == 200
    assert report.json() == {
        "total": 1,
        "by_status": {
            "new": 0,
            "in_progress": 1,
            "completed": 0,
            "rejected": 0,
        },
    }


def test_list_search_filter_and_pagination(client):
    first = create_lead(client, name="Иван Петров", phone="+79990000001")
    second = create_lead(client, name="Анна Смирнова", phone="+79990000002")
    third = create_lead(client, name="Иван Сидоров", phone="+79990000003")
    assert all(item.status_code == 201 for item in (first, second, third))

    search = client.get("/leads", params={"search": "Иван"})
    assert search.status_code == 200
    assert len(search.json()) == 2

    first_page = client.get("/leads", params={"limit": 1, "offset": 0})
    second_page = client.get("/leads", params={"limit": 1, "offset": 1})
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]

    updated = client.patch(
        f"/leads/{second.json()['id']}/status",
        json={"status": "completed"},
    )
    assert updated.status_code == 200

    filtered = client.get("/leads", params={"status": "completed"})
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["id"] == second.json()["id"]


def test_whitespace_is_trimmed_and_blank_required_fields_are_rejected(client):
    valid = client.post(
        "/leads",
        json={
            "name": "  Иван Петров  ",
            "phone": "  +79990000000  ",
            "service": "  Ремонт ноутбука  ",
            "message": "  Нужна диагностика  ",
        },
    )
    assert valid.status_code == 201
    assert valid.json()["name"] == "Иван Петров"
    assert valid.json()["phone"] == "+79990000000"
    assert valid.json()["service"] == "Ремонт ноутбука"
    assert valid.json()["message"] == "Нужна диагностика"

    invalid = client.post(
        "/leads",
        json={
            "name": "   ",
            "phone": "   ",
            "service": "  ",
            "message": "",
        },
    )
    assert invalid.status_code == 422


def test_invalid_status_and_invalid_status_filter_return_422(client):
    created = create_lead(client)
    lead_id = created.json()["id"]

    update = client.patch(
        f"/leads/{lead_id}/status",
        json={"status": "unknown"},
    )
    filtered = client.get("/leads", params={"status": "unknown"})

    assert update.status_code == 422
    assert filtered.status_code == 422


def test_missing_lead_returns_404(client):
    response = client.get("/leads/999999")
    update = client.patch(
        "/leads/999999/status",
        json={"status": "completed"},
    )

    assert response.status_code == 404
    assert update.status_code == 404
