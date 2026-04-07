from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.reports.pdf_generator import generate_report as gen_pdf
from app.constants import ReportType
from app.logger import get_logger
from app.mcp.tools.naver_datalab import get_search_trends
from app.mcp.tools.naver_shopping import search_products
from app.schemas.report import NicheAnalysisData, SeasonalData, DiagnosticsData, SEOData, CompetitorData, TrendPoint, \
    Competitor

logger = get_logger(__name__)


def _parse_trends(trends_raw: dict) -> list[TrendPoint]:
    """Парсит ответ Naver DataLab в список TrendPoint."""
    try:
        data = trends_raw["results"][0]["data"]
        return [
            TrendPoint(month=item["period"][:7], value=item["ratio"])
            for item in data
        ]
    except (KeyError, IndexError):
        return []


def _parse_competitors(products_raw: dict) -> list[Competitor]:
    """Парсит ответ Naver Shopping в список Competitor."""
    try:
        items = products_raw["items"]
        return [
            Competitor(
                name=item["title"].replace("<b>", "").replace("</b>", ""),
                price=int(item["lprice"]),
                reviews=int(item.get("reviewCount", 0)),
                link=item.get("link")
            )
            for item in items
        ]
    except (KeyError, TypeError):
        return []


async def generate_pdf_report(report_type: str, keyword: str) -> str:
    try:
        trends_raw = await get_search_trends(keyword)
        products_raw = await search_products(keyword)
        trends = _parse_trends(trends_raw)
        competitors = _parse_competitors(products_raw)
        avg_price = int(sum(c.price for c in competitors) / len(competitors)) if competitors else 0
        first = competitors[0] if competitors else None

        if report_type == "niche_analysis":
            data = NicheAnalysisData(
                keyword=keyword,
                trends=trends,
                competitors=competitors,
                summary="Анализ выполнен на основе данных Naver DataLab и Naver Shopping."
            )
        elif report_type == "seasonal":
            peak_months = [t.month[-2:] for t in sorted(trends, key=lambda x: x.value, reverse=True)[:3]]
            data = SeasonalData(
                keyword=keyword,
                trends=trends,
                peak_months=peak_months,
                price_dynamics=competitors,
                recommendations="Рекомендуется усилить продажи в пиковые месяцы."
            )
        elif report_type == "diagnostics":
            data = DiagnosticsData(
                product_name=first.name if first else keyword,
                product_price=first.price if first else 0,
                avg_competitor_price=avg_price,
                search_trend=trends,
                problems=["Недостаточно данных для полной диагностики"],
                recommendations=["Сравните цену с конкурентами", "Проверьте SEO описание"]
            )
        elif report_type == "seo":
            data = SEOData(
                original_title=first.name if first else keyword,
                original_description="Описание товара",
                keywords=[keyword] + [c.name[:10] for c in competitors[:3]],
                new_title=f"{keyword} - лучшая цена на Naver",
                new_description=f"Купите {keyword} по выгодной цене. Быстрая доставка."
            )
        elif report_type == "competitors":
            prices = [c.price for c in competitors]
            data = CompetitorData(
                keyword=keyword,
                competitors=competitors,
                avg_price=avg_price,
                min_price=min(prices) if prices else 0,
                max_price=max(prices) if prices else 0,
                summary=f"Найдено {len(competitors)} конкурентов. Средняя цена: {avg_price:,} ₩"
            )
        else:
            logger.error(f"Invalid report type: {report_type}")
            raise ValueError(f"Invalid report type: {report_type}")

        pdf_bytes = gen_pdf(ReportType(report_type), data)

        Path(settings.REPORTS_DIR).mkdir(exist_ok=True)
        filename = f"{report_type}_{uuid4().hex[:8]}.pdf"
        filepath = Path(settings.REPORTS_DIR) / filename

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"Report saved: {filepath}")
        return f"/reports-files/{filename}"
    except Exception as e:
        logger.error(f"Failed to generate report {report_type}: {e}")
        raise
