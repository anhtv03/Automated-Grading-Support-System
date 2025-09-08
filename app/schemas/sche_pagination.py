from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar("T")  # Generic type cho data

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page_no: int
    page_size: int

    model_config = {"from_attributes": True}