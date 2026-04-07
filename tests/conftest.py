import pytest
import psycopg2
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import get_db
from app.db.models import Base
from app.config import settings


def get_test_engine():
    return create_async_engine(settings.TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def client():
    test_engine = get_test_engine()
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_db(setup_db):
    yield
    conn_string = settings.TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("TRUNCATE users, products, reports CASCADE")
    cur.close()
    conn.close()


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """Регистрирует пользователя и возвращает JWT токен."""
    payload = {"email": "test@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)

    from fastapi.testclient import TestClient
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    return response.json()["access_token"]