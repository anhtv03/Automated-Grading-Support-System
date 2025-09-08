from typing import Optional, List

from pydantic import BaseModel


class SubmissionQuestionBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class SubmissionQuestionCreateRequest(SubmissionQuestionBase):
    submission_id: int
    question_name: str


class SubmissionQuestionUpdateRequest(SubmissionQuestionBase):
    id: int
    cluster_id: int


class SubmissionQuestionResponse(SubmissionQuestionBase):
    id: int
    submission_id: int
    question_name: str


class SubmissionQuestionData(SubmissionQuestionBase):
    id: int
    question_name: str
    score: float


# class SubmissionQuestionItemResponse(SubmissionQuestionBase):
#     id: int
#     question_name: str
#     ai_grading: Optional[AiGradingResponse] = None
#     expert_grading: Optional[ExpertGradingResponse] = None

class SubmissionQuestionItemResponse(SubmissionQuestionBase):
    id: int
    question_name: str
    ai_score: Optional[float] = None
    ai_comment: Optional[str] = None
    expert_score: Optional[float] = None
    expert_comment: Optional[str] = None


class SubmissionQuestionContext(SubmissionQuestionBase):
    session_id: int
    answer_id: int


class CriteriaHistoryResponse(SubmissionQuestionBase):
    submission_id: Optional[int]
    question_id: Optional[int]
    question_name: Optional[str]
    criteria_id: Optional[int]
    criteria_title: Optional[str]
    max_point: Optional[float]
    ai_score: Optional[float]
    expert_score: Optional[float]


class CriteriaRequest(SubmissionQuestionBase):
    criteria_id: int
    expert_score: Optional[float]


class CriteriaHistoryUpdateRequest(SubmissionQuestionBase):
    question_id: int
    expert_comment: Optional[str]
    criteria: List[CriteriaRequest]
