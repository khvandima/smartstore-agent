from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Union
import io

from app.api.dependencies import get_current_user
from app.constants import ReportType
from app.db.models import User
from app.reports.pdf_generator import generate_report
from app.schemas.report import NicheAnalysisData, DiagnosticsData, SEOData, SeasonalData, CompetitorData
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])
ReportData = Union[NicheAnalysisData, DiagnosticsData, SEOData, SeasonalData, CompetitorData]

@router.post('/{report_type}')
async def generate_report_endpoint(
        report_type: ReportType,
        data: ReportData,
        current_user: User = Depends(get_current_user)
):
    try:
        pdf_bytes = generate_report(report_type, data)
        logger.info(f"Report generated: type={report_type}, size={len(pdf_bytes)} bytes, user={current_user.email}")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_type}.pdf"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate report {report_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")