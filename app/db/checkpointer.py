from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

_checkpointer = None
_cm = None

async def init_checkpointer():
    global _checkpointer, _cm
    conn_string = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _cm = AsyncPostgresSaver.from_conn_string(conn_string)
    _checkpointer = await _cm.__aenter__()
    await _checkpointer.setup()
    logger.info('PostgresSaver initialized')

async def close_checkpointer():
    global _cm
    if _cm:
        await _cm.__aexit__(None, None, None)

def get_checkpointer():
    return _checkpointer