from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExamBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class ExamRequest(ExamBase):
    name: str
    session_id: int


class ExamGuideRequest(ExamBase):
    exam_id: int
    grading_guide_id: int

class ExamUpdatedRequest(ExamRequest):
    id: int


class ExamResponse(ExamBase):
    id: int
    name: str
    file_key: Optional[str] = None
    session_id: int
    created_at: Optional[datetime] = None
