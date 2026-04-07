from io import BytesIO
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from docx import Document
import pandas as pd

from qdrant_client.models import Filter, FieldCondition, MatchValue, VectorParams, Distance, PointStruct
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

class DocumentIngester:
    def __init__(self, content: bytes, filename: str, user_id: str, embedding_model: SentenceTransformer, qdrant: AsyncQdrantClient):
        self.qdrant = qdrant
        self.content = content
        self.filename = filename
        self.user_id = user_id
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.embeddings = embedding_model

    async def ingest(self) -> None:
        if Path(self.filename).suffix == '.txt':
            texts = self._load_txt()
        elif Path(self.filename).suffix in ['.docx', '.doc', '.docs']:
            texts = self._load_docx()
        elif Path(self.filename).suffix in ['.xlsx', '.xls']:
            texts = self._load_xlsx()
        else:
            logger.error(f"Unsupported file type: {self.filename}")
            raise ValueError('Unsupported file type')
        logger.info(f"Ingesting {len(texts)} documents...")
        chunks = []
        for text in texts:
            chunks.extend(self.splitter.split_text(text))
        logger.info(f"Split into {len(chunks)} chunks")
        await self._store_chunks(chunks, source=Path(self.filename).name)

    def _load_txt(self) -> list[str]:
        try:
            text = self.content.decode('utf-8').strip()
            logger.info(f"Loaded txt file: {self.filename}")
            return [text]
        except Exception as e:
            logger.error(f"Failed to load file {self.filename}: {e}")
            raise

    def _load_docx(self) -> list[str]:
        try:
            doc = Document(BytesIO(self.content))
            texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            logger.info(f"Loaded docx file: {self.filename}, paragraphs: {len(texts)}")
            return texts
        except Exception as e:
            logger.error(f"Failed to load file {self.filename}: {e}")
            raise

    def _load_xlsx(self) -> list[str]:
        texts = []
        try:
            df = pd.read_excel(BytesIO(self.content))
            for _, row in df.iterrows():
                text = ', '.join(f'{k}: {v}' for k, v in row.to_dict().items())
                texts.append(text)
            logger.info(f"Loaded xlsx file: {self.filename}")
            return texts
        except Exception as e:
            logger.error(f"Failed to load xlsx file: {self.filename}: {e}")
            raise

    async def _store_chunks(self, chunks: list[str], source: str) -> None:
        try:
            prefixed_chunks = [f"passage: {chunk}" for chunk in chunks]
            vectors = self.embeddings.encode(prefixed_chunks)
            logger.info(f"Generated {len(vectors)} embeddings for source: {source}")
            if not await self.qdrant.collection_exists(settings.QDRANT_COLLECTION_NAME):
                await self.qdrant.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {settings.QDRANT_COLLECTION_NAME}")
            else:
                logger.info(f"Collection already exists: {settings.QDRANT_COLLECTION_NAME}")
            points = [
                PointStruct(
                    id=str(uuid4()),
                    vector=vector.tolist(),
                    payload={
                        "text": chunk,
                        "user_id": self.user_id,
                        "source": source
                    }
                )
                for chunk, vector in zip(chunks, vectors)
            ]
            await self.qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points,
            )
            logger.info(f"Upserted {len(points)} points to Qdrant, source: {source}, user: {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to store chunks in Qdrant: {e}")
            raise

    async def delete_document(self, source: str) -> None:
        try:
            await self.qdrant.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="source", match=MatchValue(value=source)),
                        FieldCondition(key="user_id", match=MatchValue(value=self.user_id))
                    ]
                )
            )
            logger.info(f"Deleted chunks for source: {source}, user: {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {source}: {e}")
            raise