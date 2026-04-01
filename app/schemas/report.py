from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.constants import ReportType


class ReportResponse(BaseModel):
    id: UUID
    title: str
    report_type: ReportType
    product_id: UUID | None = None
    file_name: str
    download_url: str
    created_at: datetime