from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.db.checkpointer import init_checkpointer, close_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    yield
    await close_checkpointer()

app = FastAPI(title="SmartStore AI Advisor", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)