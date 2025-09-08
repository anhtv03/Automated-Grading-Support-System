from pydantic import BaseModel


class PlagiarismBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class PlagiarismCreateRequest(PlagiarismBase):
    source_id: int
    plagiarism_id: int
    similarity_score: float

