from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API ключи
    GROQ_API_KEY: str
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    TAVILY_API_KEY: str

    # База данных
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""
    QDRANT_HOST: str
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "smartstore_agent"

    # Приложение / JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # RAG параметры
    EMBEDDING_MODEL: str = 'multilingual-e5-large'
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    VECTOR_SIZE: int = 1024
    RERANK_MODEL: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'

    # LLM
    LLM_MODEL: str = 'llama-3.3-70b-versatile'

    # Log
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


settings = Settings()