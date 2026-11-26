from datetime import datetime, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import decode_access_token


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_login_returns_signed_short_lived_jwt(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes-long")
    response = client.post("/auth/register", json={
        "username": "Login User", "email": "login@example.com", "password": "correct horse battery",
    })
    assert response.status_code == 201

    login = client.post("/auth/login", json={"email": "LOGIN@example.com", "password": "correct horse battery"})
    assert login.status_code == 200
    result = login.json()
    assert result["token_type"] == "bearer"
    claims = decode_access_token(result["access_token"])
    assert claims["sub"] == response.json()["id"]
    assert claims["exp"] > claims["iat"]
    assert result["expires_in"] == 900


def test_login_rejects_unknown_email_and_bad_password(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes-long")
    client.post("/auth/register", json={
        "username": "Login User", "email": "login@example.com", "password": "correct horse battery",
    })
    wrong_password = client.post("/auth/login", json={"email": "login@example.com", "password": "incorrect password"})
    missing_email = client.post("/auth/login", json={"email": "missing@example.com", "password": "incorrect password"})
    assert wrong_password.status_code == missing_email.status_code == 401
    assert wrong_password.json() == missing_email.json()
    assert wrong_password.json()["code"] == "authentication_failed"


def test_login_requires_credentials_and_valid_email(client):
    assert client.post("/auth/login", json={"email": "invalid", "password": "secret"}).status_code == 422
    assert client.post("/auth/login", json={"email": "user@example.com"}).status_code == 422
