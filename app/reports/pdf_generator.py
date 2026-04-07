import base64
import io
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from app.constants import ReportType
from app.logger import get_logger
from app.schemas.report import (
    NicheAnalysisData, DiagnosticsData, SEOData,
    SeasonalData, CompetitorData
)

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
CSS_PATH = TEMPLATES_DIR / "style.css"

REPORT_TYPE_LABELS = {
    ReportType.niche_analysis: "Анализ ниши",
    ReportType.diagnostics:    "Диагностика продаж",
    ReportType.seo:            "SEO оптимизация",
    ReportType.seasonal:       "Сезонный анализ",
    ReportType.competitors:    "Анализ конкурентов",
}

plt.rcParams.update({
    'font.family':       'DejaVu Sans',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.grid':         True,
    'grid.alpha':        0.3,
    'grid.linestyle':    '--',
    'figure.dpi':        150,
})

ACCENT_COLOR  = '#00C4A1'
PRIMARY_COLOR = '#0F1923'


def _chart_to_base64(fig) -> str:
    """Конвертирует matplotlib figure в base64 строку для вставки в HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


def _build_trend_chart(trends: list, ylabel: str = "Индекс поиска") -> str:
    """Строит линейный график трендов."""
    months = [t.month for t in trends]
    values = [t.value for t in trends]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.fill_between(months, values, alpha=0.12, color=ACCENT_COLOR)
    ax.plot(months, values, color=ACCENT_COLOR, linewidth=2.5, marker='o',
            markersize=5, markerfacecolor='white', markeredgewidth=2,
            markeredgecolor=ACCENT_COLOR)

    max_idx = values.index(max(values))
    ax.annotate(
        f"Пик: {values[max_idx]:.0f}",
        xy=(months[max_idx], values[max_idx]),
        xytext=(0, 12), textcoords='offset points',
        ha='center', fontsize=8, color=PRIMARY_COLOR, fontweight='bold'
    )

    ax.set_ylabel(ylabel, fontsize=9, color='#64748B')
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.set_facecolor('#F7F9FC')
    fig.patch.set_facecolor('#F7F9FC')
    return _chart_to_base64(fig)


def _build_bar_chart(labels: list[str], values: list[float],
                     colors: list[str] | str = ACCENT_COLOR) -> str:
    """Строит столбчатый график."""
    fig, ax = plt.subplots(figsize=(10, 3.5))
    bars = ax.bar(labels, values, color=colors, alpha=0.85, width=0.6,
                  edgecolor='white', linewidth=1.5)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            f"{val:,.0f}",
            ha='center', va='bottom', fontsize=8, color=PRIMARY_COLOR
        )

    ax.tick_params(axis='x', rotation=30, labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.set_facecolor('#F7F9FC')
    fig.patch.set_facecolor('#F7F9FC')
    return _chart_to_base64(fig)


def _render_html(template_name: str, context: dict) -> str:
    """Рендерит Jinja2 шаблон."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    return env.get_template(template_name).render(**context)


def _html_to_bytes(html: str) -> bytes:
    """Конвертирует HTML в PDF байты — без сохранения на диск."""
    return HTML(string=html).write_pdf(
        stylesheets=[CSS(filename=str(CSS_PATH))]
    )


def _base_context(report_type: ReportType, title: str) -> dict:
    """Базовый контекст для всех шаблонов."""
    return {
        "title":             title,
        "report_type_label": REPORT_TYPE_LABELS[report_type],
        "generated_at":      datetime.now().strftime("%d.%m.%Y %H:%M"),
        "css_path":          str(CSS_PATH),
    }


def generate_niche_analysis(data: NicheAnalysisData) -> bytes:
    """Генерирует PDF отчёт — анализ ниши. Возвращает bytes."""
    logger.info(f"Генерация niche_analysis: {data.keyword}")
    try:
        avg_price   = sum(c.price for c in data.competitors) / len(data.competitors) if data.competitors else 0
        peak_value  = max(t.value for t in data.trends) if data.trends else 0
        trend_chart = _build_trend_chart(data.trends)

        context = _base_context(ReportType.niche_analysis, f"Анализ ниши: {data.keyword}")
        context.update({"data": data, "avg_price": avg_price,
                        "peak_value": peak_value, "trend_chart": trend_chart})

        return _html_to_bytes(_render_html("niche_analysis.html", context))
    except Exception as e:
        logger.error(f"Ошибка генерации niche_analysis: {e}")
        raise


def generate_diagnostics(data: DiagnosticsData) -> bytes:
    """Генерирует PDF отчёт — диагностика продаж. Возвращает bytes."""
    logger.info(f"Генерация diagnostics: {data.product_name}")
    try:
        trend_chart = _build_trend_chart(data.search_trend)
        price_chart = _build_bar_chart(
            labels=["Ваша цена", "Средняя цена конкурентов"],
            values=[data.product_price, data.avg_competitor_price],
            colors=[
                '#EF4444' if data.product_price > data.avg_competitor_price else ACCENT_COLOR,
                ACCENT_COLOR
            ]
        )

        context = _base_context(ReportType.diagnostics, f"Диагностика: {data.product_name}")
        context.update({"data": data, "trend_chart": trend_chart, "price_chart": price_chart})

        return _html_to_bytes(_render_html("diagnostics.html", context))
    except Exception as e:
        logger.error(f"Ошибка генерации diagnostics: {e}")
        raise


def generate_seo(data: SEOData) -> bytes:
    """Генерирует PDF отчёт — SEO оптимизация. Возвращает bytes."""
    logger.info(f"Генерация SEO: {data.original_title}")
    try:
        context = _base_context(ReportType.seo, f"SEO: {data.original_title[:40]}")
        context.update({"data": data})
        return _html_to_bytes(_render_html("seo.html", context))
    except Exception as e:
        logger.error(f"Ошибка генерации seo: {e}")
        raise


def generate_seasonal(data: SeasonalData) -> bytes:
    """Генерирует PDF отчёт — сезонный анализ. Возвращает bytes."""
    logger.info(f"Генерация seasonal: {data.keyword}")
    try:
        trend_chart = _build_trend_chart(data.trends)
        context = _base_context(ReportType.seasonal, f"Сезонность: {data.keyword}")
        context.update({"data": data, "trend_chart": trend_chart})
        return _html_to_bytes(_render_html("seasonal.html", context))
    except Exception as e:
        logger.error(f"Ошибка генерации seasonal: {e}")
        raise


def generate_competitors(data: CompetitorData) -> bytes:
    """Генерирует PDF отчёт — анализ конкурентов. Возвращает bytes."""
    logger.info(f"Генерация competitors: {data.keyword}")
    try:
        names  = [c.name[:15] + "…" if len(c.name) > 15 else c.name for c in data.competitors[:10]]
        prices = [c.price for c in data.competitors[:10]]
        price_chart = _build_bar_chart(names, prices)

        context = _base_context(ReportType.competitors, f"Конкуренты: {data.keyword}")
        context.update({"data": data, "price_chart": price_chart})
        return _html_to_bytes(_render_html("competitors.html", context))
    except Exception as e:
        logger.error(f"Ошибка генерации competitors: {e}")
        raise


GENERATORS = {
    ReportType.niche_analysis: generate_niche_analysis,
    ReportType.diagnostics:    generate_diagnostics,
    ReportType.seo:            generate_seo,
    ReportType.seasonal:       generate_seasonal,
    ReportType.competitors:    generate_competitors,
}


def generate_report(
        report_type: ReportType,
        data: NicheAnalysisData | DiagnosticsData | SEOData | SeasonalData | CompetitorData,
) -> bytes:
    """Точка входа — генерирует PDF и возвращает bytes. Файл не сохраняется на диск."""
    generator = GENERATORS.get(report_type)
    if not generator:
        raise ValueError(f"Неизвестный тип отчёта: {report_type}")
    return generator(data)