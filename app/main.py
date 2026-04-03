from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router

app = FastAPI(title="SmartStore AI Advisor")

app.include_router(auth_router)
app.include_router(chat_router)