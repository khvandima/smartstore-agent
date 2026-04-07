from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.constants import ReportType


class ReportResponse(BaseModel):
    id: UUID
    title: str
    report_type: ReportType
    product_id: UUID | None = None
    file_name: str
    download_url: str
    created_at: datetime


class TrendPoint(BaseModel):
    month: str        # "2024-01"
    value: float      # Search index 0-100


class Competitor(BaseModel):
    name: str
    price: int        # in Korean Won
    reviews: int
    link: str | None # Item link


class NicheAnalysisData(BaseModel):
    keyword: str
    trends: list[TrendPoint]
    competitors: list[Competitor]
    summary: str


class DiagnosticsData(BaseModel):
    product_name: str # название товара продавца
    product_price: int # цена продавца
    avg_competitor_price: int # средняя цена конкурентов
    search_trend: list[TrendPoint] # тренд спроса
    problems: list[str] # список выявленных проблем
    recommendations: list[str] # рекомендации


class SEOData(BaseModel):
    original_title: str # исходное название товара
    original_description: str # исходное описание
    keywords: list[str] # рекомендуемые ключевые слова
    new_title: str # новый SEO заголовок
    new_description: str # новое описание


class SeasonalData(BaseModel):
    keyword: str # ключевое слово
    trends: list[TrendPoint] # тренды по месяцам
    peak_months: list[str] # пиковые месяцы например ["11", "12"]
    price_dynamics: list[Competitor] # цены конкурентов в разные периоды
    recommendations: str # когда закупать и продавать


class CompetitorData(BaseModel):
    keyword: str # ключевое слово
    competitors: list[Competitor] # список конкурентов
    avg_price: int # средняя цена рынка
    min_price: int # минимальная цена
    max_price: int # максимальная цена
    summary: str # вывод о позиционировании

