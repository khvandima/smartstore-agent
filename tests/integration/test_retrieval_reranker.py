import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sentence_transformers import SentenceTransformer, CrossEncoder

from app.rag.retrieval import DocumentRetriever
from app.rag.reranker import Reranker
from app.config import settings


# ─── RETRIEVAL ───────────────────────────────────────────────────

def make_retriever(user_id: str = "test_user") -> DocumentRetriever:
    """Создаёт DocumentRetriever с мок Qdrant и embedding моделью."""
    mock_qdrant = AsyncMock()
    mock_embeddings = MagicMock(spec=SentenceTransformer)
    mock_embeddings.encode.return_value = MagicMock(tolist=lambda: [0.1] * 1024)

    retriever = DocumentRetriever.__new__(DocumentRetriever)
    retriever.user_id = user_id
    retriever.qdrant = mock_qdrant
    retriever.embeddings = mock_embeddings
    return retriever


def test_retriever_adds_query_prefix():
    """retrieve() добавляет префикс 'query: ' к запросу."""
    retriever = make_retriever()

    encoded_query = None

    def capture_encode(text):
        nonlocal encoded_query
        encoded_query = text
        mock = MagicMock()
        mock.tolist.return_value = [0.1] * 1024
        return mock

    retriever.embeddings.encode = capture_encode

    # Мокируем qdrant.search
    mock_result = MagicMock()
    mock_result.payload = {"text": "test chunk", "source": "test.txt"}
    mock_result.score = 0.9
    retriever.qdrant.search = AsyncMock(return_value=[mock_result])

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("термос", top_k=5)
    )

    assert encoded_query.startswith("query: ")
    assert "термос" in encoded_query


def test_retriever_filters_by_user_id():
    """retrieve() передаёт фильтр по user_id в Qdrant."""
    retriever = make_retriever(user_id="user_123")

    mock_result = MagicMock()
    mock_result.payload = {"text": "chunk", "source": "file.txt"}
    mock_result.score = 0.8
    retriever.qdrant.search = AsyncMock(return_value=[mock_result])

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("query", top_k=5)
    )

    call_kwargs = retriever.qdrant.search.call_args.kwargs
    filter_obj = call_kwargs.get("query_filter")
    assert filter_obj is not None


def test_retriever_returns_tuples():
    """retrieve() возвращает list[tuple[str, float]]."""
    retriever = make_retriever()

    mock_result = MagicMock()
    mock_result.payload = {"text": "chunk text", "source": "file.txt"}
    mock_result.score = 0.85
    retriever.qdrant.search = AsyncMock(return_value=[mock_result])

    import asyncio
    results = asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("query", top_k=5)
    )

    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert results[0][0] == "chunk text"
    assert results[0][1] == 0.85


def test_retriever_uses_top_k_times_4():
    """retrieve() запрашивает top_k * 4 результатов для reranking."""
    retriever = make_retriever()
    retriever.qdrant.search = AsyncMock(return_value=[])

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("query", top_k=5)
    )

    call_kwargs = retriever.qdrant.search.call_args.kwargs
    assert call_kwargs.get("limit") == 20  # 5 * 4


# ─── RETRIEVAL + RERANKER В СВЯЗКЕ ──────────────────────────────

def test_retrieval_reranker_pipeline():
    """Тест полного pipeline: retrieve() → rerank()."""
    # Настраиваем retriever
    retriever = make_retriever()
    candidates = [
        ("Термос 500мл отличное качество", 0.7),
        ("Купить термос дёшево", 0.5),
        ("Термос для чая корейский бренд", 0.9),
    ]
    retriever.qdrant.search = AsyncMock(return_value=[
        MagicMock(payload={"text": text, "source": "test.txt"}, score=score)
        for text, score in candidates
    ])

    import asyncio
    retrieved = asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("термос", top_k=2)
    )

    # Настраиваем reranker
    mock_cross_encoder = MagicMock(spec=CrossEncoder)
    mock_cross_encoder.predict.return_value = [0.3, 0.1, 0.9]
    reranker = Reranker(model=mock_cross_encoder)

    results = reranker.rerank("термос", retrieved, top_k=2)

    # Проверяем что вернулось top_k результатов
    assert len(results) == 2
    assert isinstance(results[0], str)
    # Лучший результат — с наивысшим score от cross-encoder
    assert results[0] == "Термос для чая корейский бренд"


def test_pipeline_empty_retrieval():
    """Если retrieval вернул пустой список — reranker возвращает []."""
    retriever = make_retriever()
    retriever.qdrant.search = AsyncMock(return_value=[])

    import asyncio
    retrieved = asyncio.get_event_loop().run_until_complete(
        retriever.retrieve("query", top_k=5)
    )

    mock_cross_encoder = MagicMock(spec=CrossEncoder)
    reranker = Reranker(model=mock_cross_encoder)

    results = reranker.rerank("query", retrieved, top_k=5)
    assert results == []
    mock_cross_encoder.predict.assert_not_called()