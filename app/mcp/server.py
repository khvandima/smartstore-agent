from fastmcp import FastMCP

from app.mcp.tools.tavily import tavily_search
from app.mcp.tools.naver_datalab import  get_search_trends
from app.mcp.tools.naver_shopping import search_products

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


if __name__ == "__main__":
    mcp.run(transport="sse", port=8001)
