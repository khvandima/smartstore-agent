import httpx
from datetime import datetime, timedelta
from app.config import settings

from app.logger import get_logger

logger = get_logger(__name__)

async def get_search_trends(keyword: str) -> list:
    headers = {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),  # год назад
        "endDate": end_date.strftime("%Y-%m-%d"),    # сегодня
        "timeUnit": "month",        # по месяцам
        "keywordGroups": [
            {
                "groupName": keyword,
                "keywords": [keyword]
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Naver DataLab API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Naver DataLab connection error: {e}")
            raise
