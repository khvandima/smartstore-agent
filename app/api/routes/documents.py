from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pathlib import Path

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.api.dependencies import get_current_user
from app.db.models import User
from app.rag.ingestion import DocumentIngester
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post('/upload')
async def upload_document(
        req: Request,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    allowed_extensions = {'.txt', '.docx', '.doc', '.xlsx', '.xls'}
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(status_code=400, detail="Filename is missing")
    content = await file.read()
    if not content:
        logger.error(f"No file found")
        raise HTTPException(status_code=404, detail="File not found")
    max_file_size = 10 * 1024 * 1024
    if len(content) > max_file_size:
        raise HTTPException(status_code=400, detail="File too large. Max size: 10MB")
    filename = file.filename
    if Path(filename).suffix.lower() not in allowed_extensions:
        logger.error(f"File extension must be {allowed_extensions}")
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {allowed_extensions}")
    ingester = DocumentIngester(content, filename, str(current_user.id), req.app.state.embedding_model, qdrant=req.app.state.qdrant)
    await ingester.ingest()
    return {'filename': filename, 'status': 'indexed'}


@router.get('/')
async def list_documents(req: Request, current_user: User = Depends(get_current_user)):
    try:
        qdrant = req.app.state.qdrant
        results, _ = await qdrant.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key='user_id', match=MatchValue(value=str(current_user.id)))]
            ),
            with_payload=True,
            limit=1000
        )
        sources = sorted({point.payload.get('source') for point in results if point.payload.get('source')})
        logger.info(f"Found {len(sources)} documents for user: {current_user.id}")
        return {'documents': sources}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.delete('/{filename}')
async def delete_document(req: Request, filename: str, current_user: User = Depends(get_current_user)):
    ingester = DocumentIngester(b"", filename, str(current_user.id), req.app.state.embedding_model, qdrant=req.app.state.qdrant)
    await ingester.delete_document(filename)
    return {'filename': filename, 'status': 'deleted'}