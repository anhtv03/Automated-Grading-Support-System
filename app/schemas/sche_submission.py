from typing import Optional, List

from fastapi import UploadFile
from pydantic import BaseModel

from app.schemas.sche_submisson_question import SubmissionQuestionItemResponse, SubmissionQuestionData


class SubmissionBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class SubmissionCreateRequest(SubmissionBase):
    session_id: int
    name: str

class SubmissionItemCreateRequest(SubmissionBase):
    name: str
    file: UploadFile

class SubmissionItemResponse(SubmissionBase):
    id: int
    name: str
    content: str

class SubmissionCreate(SubmissionBase):
    session_id: int
    name: str
    content: str
    file_key: str

class SubmissionItemDetailResponse(SubmissionBase):
    id: int
    name: str
    session_id: int
    type: Optional[str] = None
    file_key: Optional[str] = None
    final_score: Optional[float] = None
    ai_plagiarism_score: Optional[float] = None
    question_response: List[SubmissionQuestionItemResponse]


class SubmissionAIDetector(SubmissionBase):
    ai_detected_count: int
    total_submissions: int


class SubmissionResponse(SubmissionBase):
    id: int
    name: str
    file_key: Optional[str] = None
    session_id: Optional[int] = None
    content: Optional[str] = None

class SubmissionPlagiarismResponse(SubmissionBase):
    id: int
    name: str
    file_key: str
    questions: List[SubmissionQuestionData]