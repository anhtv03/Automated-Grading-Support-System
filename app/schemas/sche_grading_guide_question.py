from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class GradingGuideQuestionBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class GuideQuestionRequestParams(BaseModel):
    sort_by: Optional[str] = 'created_at'
    order: Optional[str] = 'desc'
    options: Optional[str] = None  # "status:active&age=18&valid=true&name=abc"


class GuideQuestionUpdateRequest(GradingGuideQuestionBase):
    input_prompt: Optional[str] = None
    content: Optional[str] = None


class GuideQuestionCreateRequest(GradingGuideQuestionBase):
    grading_guide_id: int
    exam_question_ids: Optional[List[int]] = None

class GradingGuideQuestionResponse(GradingGuideQuestionBase):
    id: int
    grading_guide_id: Optional[int]
    exam_question_id: Optional[int]
    question_name: Optional[str] = None
    input_prompt: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    criteria: Optional[Dict[str, Any]] = None
