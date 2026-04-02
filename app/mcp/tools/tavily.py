from tavily import TavilyClient
from app.config import settings
from app.logger import get_logger


logger = get_logger(__name__)
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)  # ← другое имя


def tavily_search(query: str) -> str:
    """Search the web for information about the given query."""
    logger.info(f"Tavily search: {query}")
    try:
        results = tavily_client.search(
            query=query,
            max_results=settings.TAVILY_SEARCH_MAX_RESULTS
        )
        logger.info(f"Tavily search completed: {len(results.get('results', []))} results")
        return str(results)
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        raise