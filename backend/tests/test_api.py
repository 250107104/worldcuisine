"""HTTP integration tests backed by PostgreSQL."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import create_access_token

U = "/users/u1"           # demo user created by the seed
CARBONARA, PIZZA, TERIYAKI = "1001", "1002", "1003"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes-long")
    token, _ = create_access_token("u1")
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


def error_code(response):
    assert response.json()["code"]
    return response.json()["code"]
