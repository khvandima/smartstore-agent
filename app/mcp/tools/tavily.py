from tavily import TavilyClient
from app.config import settings

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)  # ← другое имя


def tavily_search(query: str) -> str:
    """Search the web for information about the given query."""
    results = tavily_client.search(query=query, max_results=settings.TAVILY_SEARCH_MAX_RESULTS)
    return str(results)