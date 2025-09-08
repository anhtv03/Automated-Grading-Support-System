from pydantic import BaseModel


class ExpertGradingBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class ExpertGradingResponse(ExpertGradingBase):
    id: int
    score: float
    explain: str
