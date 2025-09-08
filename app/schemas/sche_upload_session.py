from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UploadSessionBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class UploadSessionCreateRequest(UploadSessionBase):
    name: str
    semester_id: Optional[int] = None
    parent_session_id: Optional[int] = None
    type: Optional[str] = None


class UploadSessionUpdateRequest(UploadSessionBase):
    id: int
    name: str
    status: str

class UploadSessionUpdateTaskStatus(UploadSessionBase):
    id: int
    status: str

class UploadSessionResponse(UploadSessionBase):
    id: int
    name: str
    status: str
    parent_session_id: Optional[int] = None
    grading_status: str
    ai_detector_status: str
    plagiarism_status: str
    created_at: datetime
    task_ai: Optional[str] = None
    task_plagiarism: Optional[str] = None
    task_grading: Optional[str] = None

    # complete
    # not_start
    # failed
