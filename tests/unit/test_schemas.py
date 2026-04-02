from pydantic import ValidationError
import pytest
from uuid import uuid4

from app.constants import ReportType
from app.schemas.chat import ChatRequest
from app.schemas.user import UserCreate


def test_user_create():
    with pytest.raises(ValidationError):
        UserCreate(email='not_an_email', password='123')


def test_chat_request_valid():
    request = ChatRequest(query='test', thread_id=uuid4())
    assert request.query == "test"


def test_report_type_values():
    assert "niche_analysis" in [r.value for r in ReportType]