from typing import Optional, List

from pydantic import BaseModel


class MaterialBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class DuplicateMaterialsRequest(BaseModel):
    material_ids: List[int]
    old_exam_question_id: int
    new_exam_question_id: int

class MaterialContentResponse(MaterialBase):
    id: int
    title: str
    file_key: Optional[str] = None
    exam_question_id: int
