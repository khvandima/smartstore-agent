from fastmcp import FastMCP
from app.mcp.tools.tavily import tavily_search
from app.mcp.tools.naver_datalab import  get_search_trends

mcp = FastMCP('smartstore-advisor')

@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for information about the given query."""
    return tavily_search(query)


@mcp.tool()
async def search_naver_trends(keyword: str) -> str:
    """Get search trend data for a keyword from Naver DataLab."""
    result = await get_search_trends(keyword)
    return str(result)

