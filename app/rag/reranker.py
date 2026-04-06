from sentence_transformers import CrossEncoder

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    def __init__(self, model: CrossEncoder):
        self.model = model

    def rerank(self, query: str, candidates: list[tuple[str, float]], top_k: int = settings.TOP_K) -> list[str]:
        if not candidates:
            logger.warning("No candidates to rerank")
            return []
        pairs = [(query, text) for text, score in candidates]
        scores = self.model.predict(pairs)
        for text, old_score in candidates:
            logger.info(f"Before rerank score: {old_score:.3f}")
        ranked = sorted(
            zip([text for text, _ in candidates], scores),
            key=lambda x: x[1],  # сортируем по новому score
            reverse=True          # по убыванию
        )
        if top_k > len(ranked):
            logger.warning(f"top_k={top_k} > candidates={len(ranked)}, returning all")
        for text, new_score in ranked[:top_k]:
            logger.info(f"After rerank score: {new_score:.3f}")
        return [text for text, score in ranked[:top_k]]