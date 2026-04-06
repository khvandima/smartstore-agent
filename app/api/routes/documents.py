from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pathlib import Path

from app.api.dependencies import get_current_user
from app.db.models import User
from app.logger import get_logger
from app.rag.ingestion import DocumentIngester

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post('/upload')
async def upload_document(
        req: Request,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    ALLOWED_EXTENSIONS = {'.txt', '.docx', '.doc', '.xlsx', '.xls'}
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(status_code=400, detail="Filename is missing")
    content = await file.read()
    if not content:
        logger.error(f"No file found")
        raise HTTPException(status_code=404, detail="File not found")
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size: 10MB")
    filename = file.filename
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.error(f"File extension must be {ALLOWED_EXTENSIONS}")
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}")
    ingester = DocumentIngester(content, filename, str(current_user.id), req.app.state.embedding_model)
    await ingester.ingest()
    return {'filename': filename, 'status': 'indexed'}

@router.delete('/{filename}')
async def delete_document(req: Request, filename: str, current_user: User = Depends(get_current_user)):
    ingester = DocumentIngester(b"", filename, str(current_user.id), req.app.state.embedding_model)
    await ingester.delete_document(filename)
    return {'filename': filename, 'status': 'deleted'}