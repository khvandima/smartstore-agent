from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage

from app.db.checkpointer import get_checkpointer
from app.db.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.dependencies import get_current_user
from app.agent.mcp_client import get_mcp_tools
from app.agent.graph import build_graph

from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post('/')
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)) -> ChatResponse:
    checkpointer = get_checkpointer()
    logger.info(f"Chat request from user: {current_user.email}, thread: {request.thread_id}")

    try:
        tools, client = await get_mcp_tools()
        graph = build_graph(tools, checkpointer=checkpointer)

        config = {'configurable': {'thread_id': str(request.thread_id)}}

        result = await graph.ainvoke({
            'messages': [HumanMessage(content=request.query)],
            'user_id': str(current_user.id),
            'thread_id': str(request.thread_id),
            'report_path': None,
            'report_type': None,
        }, config=config)

        last_message = result['messages'][-1]
        logger.info(f'Chat response ready for user: {current_user.email}')

        return ChatResponse(
            response=last_message.content,
            thread_id=request.thread_id,
            report_id=None
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail='Agent unavailable')

