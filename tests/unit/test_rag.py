from unittest.mock import MagicMock, AsyncMock, patch
from sentence_transformers import CrossEncoder, SentenceTransformer

from app.rag.reranker import Reranker
from app.config import settings


def test_rerank_empty_candidates():
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.9, 0.1, 0.5]
    reranker = Reranker(model=mock_model)
    res = reranker.rerank(query='', candidates=[], top_k=settings.TOP_K)
    assert res == []


def test_rerank_returns_top_k():
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.9, 0.7, 0.5]
    candidates = [
        ("Текст чанка 1", 0.9),
        ("Текст чанка 2", 0.7),
        ("Текст чанка 3", 0.5)
    ]
    reranker = Reranker(model=mock_model)
    res = reranker.rerank(query='', candidates=candidates, top_k=2)
    assert len(res) == 2


def test_rerank_sorted_by_score():
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.5, 0.3, 0.9]
    candidates = [("text_a", 0.5), ("text_b", 0.3), ("text_c", 0.9)]
    reranker = Reranker(mock_model)
    res = reranker.rerank(query='', candidates=candidates, top_k=3)
    assert res[0] == "text_c"




