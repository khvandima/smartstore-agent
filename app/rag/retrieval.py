from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class DocumentRetriever:
    def __init__(self, user_id: str, embedding_model: SentenceTransformer):
        self.user_id = user_id
        self.qdrant = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        self.embeddings = embedding_model

    async def retrieve(self, query: str, top_k: int = settings.TOP_K) -> list[tuple[str, float]]:
        logger.info(f'Query length: {len(query)}')
        prefixed_query = f"query: {query.strip()}"
        vector = self.embeddings.encode(prefixed_query).tolist()
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=self.user_id)
                )
            ]
        )
        try:
            results = await self.qdrant.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=vector,
                query_filter=query_filter,
                limit=top_k * 4
            )
            for point in results:
                logger.info(f"Retrieved chunk score: {point.score:.3f}, source: {point.payload.get('source')}")
            return [(point.payload["text"], point.score) for point in results]
        except Exception as e:
            logger.error(f'Failed to retrieve results: {e}')
            raise
