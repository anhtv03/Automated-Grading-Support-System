from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class UserBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class GradingGuideRequest(UserBase):
    name: str
    type: str
    session_id: int


class GradingGuideUpdateRequest(GradingGuideRequest):
    id: int


class GradingGuideSuggestRequest(UserBase):
    prompt: str
    guide_question_id: int
    criteria: Optional[Dict[str, Any]] = None


class GradingGuideGenerateRequest(UserBase):
    grading_guide_id: int
    exam_question_id: int
    prompt: str
    criteria: Optional[Dict[str, Any]] = None


class GradingGuideGeneratePromptRequest(GradingGuideSuggestRequest):
    question: Optional[str] = None


class GradingGuideGenerateQuestionRequest(GradingGuideGenerateRequest):
    grading_guide_question_id: Optional[int] = None

class GradingGuideResponse(UserBase):
    id: int
    name: str
    file_key: Optional[str] = None
    type: Optional[str] = None
    session_id: int


class GradingGuideResponsePageResponse(GradingGuideResponse):
    created_at: Optional[datetime]

class GradingGuideCriteriaResponse(UserBase):
    name: Optional[str] = None
    max_point: Optional[float] = None
    question_number: Optional[int] = None


class GradingGuideSuggestResponse(UserBase):
    input_suggest: Optional[str] = None
    question_suggest: Optional[List[str]] = None
