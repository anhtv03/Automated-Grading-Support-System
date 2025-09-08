from typing import Optional
from typing import List
from pydantic import BaseModel

class CriteriaBaseModel(BaseModel):
    model_config = {
        "from_attributes": True
    }

class SubmissionQuestionBaseModel(BaseModel):
    model_config = {
        "from_attributes": True
    }

class SubmissionBaseModel(BaseModel):
    model_config = {
        "from_attributes": True
    }

# Định nghĩa response models
class CriteriaResponse(CriteriaBaseModel):
    criteria_id: int
    expert_score: Optional[float] = None

class SubmissionQuestionResponse(SubmissionQuestionBaseModel):
    id: int
    question_name: str
    expert_comment: Optional[str] = None
    criteria: Optional[List[CriteriaResponse]] = []

class SubmissionStatistic(SubmissionBaseModel):
    id: int
    name: str
    questions: Optional[List[SubmissionQuestionResponse]] = []