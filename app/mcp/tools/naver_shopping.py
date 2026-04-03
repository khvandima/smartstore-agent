import httpx
from app.config import settings

from app.logger import get_logger

logger = get_logger(__name__)


async def search_products(keyword: str) -> list:
    """
    Search for products on Naver Shopping by keyword.
    Returns list of products with prices, ratings, and review counts
    for competitor analysis.
    """
    headers = {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

    params = {
        'query': keyword,
        'display': 20,
        'sort': 'sim'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://openapi.naver.com/v1/search/shop.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Naver Shopping API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Naver Shopping connection error: {e}")
            raise