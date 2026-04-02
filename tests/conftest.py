import pytest
import psycopg2
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import get_db
from app.config import settings


def get_test_engine():
    return create_async_engine(settings.TEST_DATABASE_URL)


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
def clean_db():
    yield
    conn = psycopg2.connect(
        "postgresql://naver_user:naver_password@localhost:5432/naver_advisor_test"
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("TRUNCATE users, products, reports CASCADE")
    cur.close()
    conn.close()