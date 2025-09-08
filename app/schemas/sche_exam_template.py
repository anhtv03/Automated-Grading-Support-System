from typing import Optional

from pydantic import BaseModel


class AnswerTemplateBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class AnswerTemplateRequest(AnswerTemplateBase):
    name: str
    session_id: int


class AnswerTemplateCreateRequest(AnswerTemplateBase):
    name: str
    file_key: str
    session_id: int


class AnswerTemplateResponse(AnswerTemplateBase):
    id: int
    name: str
    file_key: Optional[str] = None
    session_id: int
