from typing import TypeVar

from pydantic import BaseModel


class BaseRequest(BaseModel):
    session_id: int


RequestT = TypeVar("RequestT")  # For DB model (ExamTemplate, Submission, etc.)
ResponseT = TypeVar("ResponseT")  # For Pydantic response (ExamTemplateResponse, etc.)
