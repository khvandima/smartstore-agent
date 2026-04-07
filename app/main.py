from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pathlib import Path

from contextlib import asynccontextmanager

from langchain_groq import ChatGroq
from qdrant_client import AsyncQdrantClient

from sentence_transformers import SentenceTransformer, CrossEncoder
from app.rag.reranker import Reranker
from app.agent.mcp_client import get_mcp_tools
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.reports import router as reports_router
from app.db.checkpointer import init_checkpointer, close_checkpointer, get_checkpointer
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    Path(settings.REPORTS_DIR).mkdir(exist_ok=True)
    tools, client = await get_mcp_tools()
    app.state.mcp_client = client
    app.state.tools = tools
    app.state.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    app.state.reranker = Reranker(model=CrossEncoder(settings.RERANK_MODEL))
    app.state.qdrant = AsyncQdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )
    yield
    await close_checkpointer()
    await client.close()

app = FastAPI(title="SmartStore AI Advisor", lifespan=lifespan)

# Сначала middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(reports_router)

@app.get("/health")
async def health_check(req: Request):
    """Health check endpoint — проверяет доступность всех компонентов."""
    status = {"status": "ok", "components": {}}

    # Проверяем Qdrant
    try:
        await req.app.state.qdrant.get_collections()
        status["components"]["qdrant"] = "ok"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        status["components"]["qdrant"] = "error"
        status["status"] = "degraded"

    # Проверяем LLM
    try:
        from langchain_core.messages import HumanMessage
        test_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.1
        )
        response = await test_llm.ainvoke([HumanMessage(content="Reply with OK")])
        if response.content:
            status["components"]["llm"] = "ok"
        else:
            status["components"]["llm"] = "error"
            status["status"] = "degraded"
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        status["components"]["llm"] = "error"
        status["status"] = "degraded"

    # Проверяем checkpointer (PostgreSQL)
    try:
        checkpointer = get_checkpointer()
        if checkpointer:
            status["components"]["postgres"] = "ok"
        else:
            status["components"]["postgres"] = "error"
            status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        status["components"]["postgres"] = "error"
        status["status"] = "degraded"

    code = 200 if status["status"] == "ok" else 503
    return JSONResponse(content=status, status_code=code)

# StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

app.mount("/reports-files", StaticFiles(directory=settings.REPORTS_DIR), name="reports")