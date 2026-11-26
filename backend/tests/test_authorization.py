"""Authorization checks for ownership and administrator-only operations."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_engine
from app.main import app
from app.models import User
from app.security import create_access_token


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "authorization-test-secret-at-least-32-bytes")
    with TestClient(app) as client:
        yield client


def bearer(user_id: str) -> dict[str, str]:
    token, _ = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_access_another_users_resources(auth_client):
    own = auth_client.get("/users/u1/stats", headers=bearer("u1"))
    other = auth_client.get("/users/u1/stats", headers=bearer("u2"))
    missing = auth_client.get("/users/u1/stats")
    assert own.status_code == 200
    assert other.status_code == 403
    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"


def test_only_administrators_can_change_catalog_or_reset(auth_client):
    user_headers = bearer("u1")
    dish_body = {
        "name": "Admin Gate Test", "country_id": "italy", "category": "Pasta",
        "ingredients": [{"name": "flour", "measure": "1 cup"}],
        "instructions": "Mix and cook until done.",
    }
    assert auth_client.post("/dishes", json=dish_body, headers=user_headers).status_code == 403
    assert auth_client.post("/admin/reset", headers=user_headers).status_code == 403

    with Session(get_engine()) as session, session.begin():
        session.get(User, "u1").role = "admin"
    admin_headers = bearer("u1")
    assert auth_client.post("/dishes", json=dish_body, headers=admin_headers).status_code == 201
    assert auth_client.post("/admin/reset", headers=admin_headers).status_code == 200
