from typing import Optional, List

from pydantic import BaseModel


class ScoreHistoryBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class ScoreHistoryCreateResponse(ScoreHistoryBase):
    submission_ids: Optional[List[int]]
    grading_guide_id: Optional[int]

class TotalScoreHistoryResponse(ScoreHistoryBase):
    ai_total_score: Optional[float] = 0
    expert_total_score: Optional[float] = 0
