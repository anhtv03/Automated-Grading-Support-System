from pydantic import BaseModel


class AiGradingBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class AiGradingResponse(AiGradingBase):
    id: int
    score: float
    explain: str
