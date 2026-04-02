from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq

from app.config import settings
from app.agent.state import AgentState
from app.logger import get_logger

logger = get_logger(__name__)

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.LLM_MODEL,
)


def build_graph(tools: list):
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def agent_node(state: AgentState) -> dict:
        last_message = state['messages'][-1]
        logger.info(f"Agent received message: {last_message.content[:100]}")

        try:
            response = llm_with_tools.invoke(state['messages'])
            logger.info(f"Agent response ready, tool_calls: {len(response.tool_calls)}")
            return {'messages': [response]}
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise

    graph = StateGraph(AgentState)

    graph.add_node('agent', agent_node)
    graph.add_node('tools', tool_node)

    graph.set_entry_point('agent')

    graph.add_conditional_edges('agent', tools_condition)
    graph.add_edge('tools', 'agent')

    return graph.compile()
