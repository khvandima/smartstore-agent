from fastapi import FastAPI
from contextlib import asynccontextmanager

from sentence_transformers import SentenceTransformer, CrossEncoder
from app.rag.reranker import Reranker
from app.agent.mcp_client import get_mcp_tools
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.db.checkpointer import init_checkpointer, close_checkpointer
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    tools, client = await get_mcp_tools()
    app.state.mcp_client = client
    app.state.tools = tools
    app.state.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    app.state.reranker = Reranker(model=CrossEncoder(settings.RERANK_MODEL))
    yield
    await close_checkpointer()
    await client.close()

app = FastAPI(title="SmartStore AI Advisor", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)