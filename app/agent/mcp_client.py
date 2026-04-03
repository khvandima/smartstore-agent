from langchain_mcp_adapters.client import MultiServerMCPClient
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


async def get_mcp_tools():
    try:
        client = MultiServerMCPClient({
            'smartstore': {
                'url': settings.MCP_SERVER_URL,
                'transport': 'sse',
            }
        })
        tools = await client.get_tools()
        logger.info(f"Tool names: {[t.name for t in tools]}")
        logger.info(f"Connected to MCP server, tools loaded: {len(tools)}")
        return tools, client
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        raise
