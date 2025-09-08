from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.schemas.sche_submission import SubmissionResponse, SubmissionPlagiarismResponse


class PlagiarismResultBase(BaseModel):
    model_config = {
        "from_attributes": True
    }

class PlagiarismResultItem(PlagiarismResultBase):
    source: SubmissionResponse
    plagiarism: SubmissionResponse
    similarity_score: float


class PlagiarismDetailResponse(PlagiarismResultBase):
    source: SubmissionResponse
    plagiarism: List[SubmissionPlagiarismResponse]

class PlagiarismQuestionDetail(PlagiarismResultBase):
    source: SubmissionResponse
    plagiarism: SubmissionResponse
    similarity_score: float