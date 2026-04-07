from fastmcp import FastMCP

from app.mcp.tools.tavily import tavily_search
from app.mcp.tools.naver_datalab import  get_search_trends
from app.mcp.tools.naver_shopping import search_products
from app.mcp.tools.report_generator import generate_pdf_report

from app.logger import get_logger

logger = get_logger(__name__)

mcp = FastMCP('smartstore-advisor')

@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for information about the given query."""
    return tavily_search(query)


@mcp.tool()
async def naver_trends(keyword: str) -> str:
    """Get search trend data for a keyword from Naver DataLab."""
    result = await get_search_trends(keyword)
    return str(result)


@mcp.tool()
async def naver_shopping(keyword: str) -> str:
    """Search for products on Naver Shopping for competitor analysis."""
    logger.info(f"naver_shopping called with keyword: {keyword}")
    result = await search_products(keyword)
    return str(result)


@mcp.tool()
async def generate_report(report_type: str, keyword: str) -> str:
    """Generate a PDF report for a keyword.
    report_type must be one of: niche_analysis, diagnostics, seo, seasonal, competitors.
    keyword should be in Korean for best results.
    Returns download URL for the generated PDF."""
    logger.info(f"generate_report called: type={report_type}, keyword={keyword}")
    return await generate_pdf_report(report_type, keyword)


if __name__ == "__main__":
    mcp.run(transport="sse", port=8001)
