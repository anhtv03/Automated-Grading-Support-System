from typing import Optional

from pydantic import BaseModel


class CriteriaBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class CriteriaResponse(CriteriaBase):
    id: int
    name: Optional[str] = None
    grading_guide_id: Optional[int] = None
    question_number: Optional[int] = None
