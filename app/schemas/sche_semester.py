from datetime import datetime

from pydantic import BaseModel


class SemesterBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class SemesterCreateRequest(SemesterBase):
    name: str
    type: str
    # sm = semester
    # gg = grading guide
    # ex = exam



class SemesterUpdateRequest(SemesterBase):
    id: int
    name: str
    status: str
    type: str


class SemesterResponse(SemesterBase):
    id: int
    name: str
    status: str
    type: str
    created_at: datetime
