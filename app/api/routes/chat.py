from fastapi import APIRouter, HTTPException, Depends, Request
from langchain_core.messages import HumanMessage

from app.db.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.dependencies import get_current_user

from app.rag.reranker import Reranker
from app.rag.retrieval import DocumentRetriever
from app.agent.graph import build_graph
from app.db.checkpointer import get_checkpointer
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post('/')
async def chat(req: Request, request: ChatRequest, current_user: User = Depends(get_current_user)) -> ChatResponse:

    logger.info(f"Chat request from user: {current_user.email}, thread: {request.thread_id}")
    user_id = str(current_user.id)

    async def search_user_docs(query: str) -> str:
        """Search in user's personal documents uploaded to the system."""
        retriever = DocumentRetriever(
            user_id=user_id,
            embedding_model=req.app.state.embedding_model
        )
        reranker = req.app.state.reranker
        candidates = await retriever.retrieve(query)
        results = reranker.rerank(query, candidates)
        return "\n\n".join(results)

    tools = req.app.state.tools + [search_user_docs]
    graph = build_graph(tools, checkpointer=get_checkpointer())

    try:
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

