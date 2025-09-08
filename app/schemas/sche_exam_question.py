from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel


class ExamQuestionBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class ExamRequestParams(BaseModel):
    sort_by: Optional[str] = 'created_at'
    order: Optional[str] = 'desc'
    options: Optional[str] = None  # "status:active&age=18&valid=true&name=abc"


class ExamQuestionGetRequest(ExamQuestionBase):
    exam_id: int
    question_name: str


class ExamQuestionGenerateRequest(ExamQuestionBase):
    prompt: str
    exam_question_id: int
    criteria: Optional[Dict[str, Any]] = None


class ExamQuestionGeneratePromptRequest(ExamQuestionGenerateRequest):
    question: Optional[str] = None


class ExamQuestionRequest(ExamQuestionGetRequest):
    criteria: Optional[Dict[str, Any]] = None


class ExamQuestionUpdateRequest(ExamQuestionBase):
    input_prompt: Optional[str] = None
    content: Optional[str] = None


class ExamQuestionGenerateResponse(ExamQuestionBase):
    id: int
    question_name: str
    input_prompt: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    criteria: Optional[Dict[str, Any]] = None
