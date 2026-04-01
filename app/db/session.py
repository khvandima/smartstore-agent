from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Движок — одиночка на всё приложение
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # True = логировать все SQL запросы
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты не протухают после commit
)

# Dependency для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session  # ← передаём сессию в endpoint
        # после yield — автоматически закрывается