import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_register_success(client: TestClient):
    payload = {
        'email': 'email@example.com',
        'password': 'password_123',
    }

    response = client.post('/auth/register', json=payload)
    data = response.json()

    assert response.status_code == 200
    assert 'id' in data
    assert 'email' in data
    assert data['email'] == payload['email']


def test_register_duplicate(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123"
    }

    # 1. Регистрируем пользователя первый раз
    first_response = client.post("/auth/register", json=payload)

    # 2. Регистрируем того же пользователя второй раз
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "User already exists"
