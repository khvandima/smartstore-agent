import io
import pytest
from fastapi.testclient import TestClient
from app.main import app


# ─── ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ────────────────────────────────────

def register_and_login(client: TestClient) -> str:
    """Регистрирует пользователя и возвращает JWT токен."""
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── AUTH ────────────────────────────────────────────────────────

def test_register_success(client: TestClient):
    payload = {'email': 'email@example.com', 'password': 'password_123'}
    response = client.post('/auth/register', json=payload)
    data = response.json()

    assert response.status_code == 200
    assert 'id' in data
    assert 'email' in data
    assert data['email'] == payload['email']


def test_register_duplicate(client: TestClient):
    payload = {"email": "duplicate@example.com", "password": "password123"}
    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "User already exists"


def test_login_success(client: TestClient):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "password123"
    })
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"}
    )
    data = response.json()

    assert response.status_code == 200
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post("/auth/register", json={
        "email": "wrong@example.com",
        "password": "password123"
    })
    response = client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "password123"}
    )
    assert response.status_code == 401


# ─── HEALTH CHECK ────────────────────────────────────────────────

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "qdrant" in data["components"]
    assert "postgres" in data["components"]


# ─── DOCUMENTS ───────────────────────────────────────────────────

def test_upload_requires_auth(client: TestClient):
    """Загрузка без токена должна вернуть 401."""
    response = client.post("/documents/upload", files={
        "file": ("test.txt", b"content", "text/plain")
    })
    assert response.status_code == 401


def test_upload_unsupported_type(client: TestClient):
    """Загрузка PDF должна вернуть 400."""
    token = register_and_login(client)
    response = client.post(
        "/documents/upload",
        headers=auth_headers(token),
        files={"file": ("report.pdf", b"pdf content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_upload_empty_file(client: TestClient):
    """Загрузка пустого файла должна вернуть 400."""
    token = register_and_login(client)
    response = client.post(
        "/documents/upload",
        headers=auth_headers(token),
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400


def test_upload_file_too_large(client: TestClient):
    """Загрузка файла больше 10MB должна вернуть 400."""
    token = register_and_login(client)
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    response = client.post(
        "/documents/upload",
        headers=auth_headers(token),
        files={"file": ("large.txt", large_content, "text/plain")}
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"]


def test_list_documents_requires_auth(client: TestClient):
    """Получение списка документов без токена должно вернуть 401."""
    response = client.get("/documents/")
    assert response.status_code == 401


def test_delete_document_requires_auth(client: TestClient):
    """Удаление документа без токена должно вернуть 401."""
    response = client.delete("/documents/test.txt")
    assert response.status_code == 401


# ─── REPORTS ─────────────────────────────────────────────────────

def test_generate_report_requires_auth(client: TestClient):
    """Генерация отчёта без токена должна вернуть 401."""
    response = client.post("/reports/niche_analysis", json={
        "keyword": "test",
        "trends": [],
        "competitors": [],
        "summary": "test"
    })
    assert response.status_code == 401


def test_generate_report_invalid_type(client: TestClient):
    """Генерация отчёта с неверным типом должна вернуть 422."""
    token = register_and_login(client)
    response = client.post(
        "/reports/invalid_type",
        headers=auth_headers(token),
        json={}
    )
    assert response.status_code == 422