from typing import TypedDict, Annotated
from langgraph.graph import add_messages

from app.constants import ReportType


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    thread_id: str
    report_path: str | None
    report_type: ReportType | None


